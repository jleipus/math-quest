variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "europe-north1"
}

variable "image_tag" {
  description = "Image version tag to deploy (e.g. v1.0.0)"
  type        = string
}

variable "llm_provider" {
  description = "LLM provider: claude or gemini"
  type        = string
  default     = "claude"
}

variable "claude_api_key" {
  description = "Anthropic Claude API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "gemini_api_key" {
  description = "Google Gemini API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "extra_allowed_origins" {
  description = "Additional CORS origins beyond the auto-detected frontend URL (JSON array string, e.g. '[\"https://example.com\"]')"
  type        = string
  default     = "[]"
}

variable "api_key" {
  description = "Shared API key sent by the frontend as X-API-Key. Leave empty to disable the check."
  type        = string
  sensitive   = true
  default     = ""
}

variable "firebase_service_account_json" {
  description = "Firebase Admin SDK service account JSON (as a single-line string). Required for Firebase Auth token verification."
  type        = string
  sensitive   = true
  default     = ""
}
