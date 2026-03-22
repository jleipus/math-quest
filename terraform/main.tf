terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  backend "gcs" {
    bucket = "mathquest-tfstate"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}


resource "google_cloud_run_v2_service" "backend" {
  name     = "mathquest-backend"
  location = var.region

  deletion_protection = false

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/mathquest/mathquest-backend:${var.image_tag}"

      resources {
        limits = {
          memory = "1Gi"
        }
      }

      ports {
        container_port = 8080
      }

      env {
        name  = "DAIS_LLM_PROVIDER"
        value = var.llm_provider
      }
      env {
        name  = "DAIS_CLAUDE_API_KEY"
        value = var.claude_api_key
      }
      env {
        name  = "DAIS_GEMINI_API_KEY"
        value = var.gemini_api_key
      }
      env {
        name  = "DAIS_FIREBASE_SERVICE_ACCOUNT_JSON"
        value = var.firebase_service_account_json
      }
      env {
        name  = "DAIS_ALLOWED_ORIGINS"
        value = var.allowed_origins # e.g. '["https://yourdomain.com"]' or '["*"]'
      }
    }
  }
}

resource "google_cloud_run_v2_service" "frontend" {
  name     = "mathquest-frontend"
  location = var.region

  deletion_protection = false

  template {
    scaling {
      max_instance_count = 1
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/mathquest/mathquest-frontend:${var.image_tag}"

      ports {
        container_port = 3000
      }

    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "frontend_url" {
  description = "Public URL of the frontend Cloud Run service"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "backend_url" {
  description = "Public URL of the backend Cloud Run service"
  value       = google_cloud_run_v2_service.backend.uri
}
