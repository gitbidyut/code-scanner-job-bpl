variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project prefix"
  type        = string
  default     = "scanner-bpl"
}

variable "artifact_bucket_name" {
  description = "S3 bucket name for CodePipeline artifacts (must be globally unique)"
  type        = string
  default     = "bpl-ml-artifacts" # set via -var or terraform.tfvars
}

variable "codecommit_repo_name" {
  description = "Name for CodeCommit repository"
  type        = string
  default     = "file-scanner-repo-bpl"
}

variable "codecommit_branch" {
  description = "Branch to use"
  type        = string
  default     = "main"
}


variable "model_artifact_s3" {
  description = "S3 path to trained model"
  default= "s3://ml-training-bucket-bpl/output/file-scanner-1765795244/output/"
}

variable "sklearn_image_uri" {
  default = "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.2-1-cpu-py3"
}
