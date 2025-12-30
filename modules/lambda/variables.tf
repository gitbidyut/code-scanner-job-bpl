variable "lambda_name" {
  description = "Lambda function name"
  type        = string
  default     = "disable-access-key-bpl"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}