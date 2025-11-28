variable "environment" {
  type = string
}

variable "subscription_id" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "acr_name" {
  type = string
}

variable "acr_username" {
  type = string
}

variable "acr_password" {
  type = string
  sensitive = true
}

variable "image_tag" {
  type = string
}

variable "aibridge_base_url" {
  type = string
}

variable "agents_base_url" {
  type = string
}

variable "salesforce_base_url" {
  type = string
}

variable "theme" {
  type = string
  default = ""
}

