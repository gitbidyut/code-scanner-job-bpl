############################
# IAM Role for CodeBuild
############################
data "aws_iam_policy_document" "codebuild_assume" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["codebuild.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "codebuild_role" {
  name               = "scanner-bpl-codebuild-role"
  assume_role_policy = data.aws_iam_policy_document.codebuild_assume.json
}

data "aws_iam_policy_document" "codebuild_policy" {
  statement {
    sid    = "SageMakerS3Logs"
    effect = "Allow"
    actions = [
       "sagemaker:InvokeEndpoint",
       "logs:CreateLogGroup",
       "logs:CreateLogStream",
       "logs:PutLogEvents",
       "s3:*",
       "lambda:InvokeFunction"
    ]
    resources = ["*"]
  }
}
resource "aws_iam_role_policy" "codebuild_policy_attach" {
  name   = "scanner-bpl-codebuild-policy1"
  role   = aws_iam_role.codebuild_role.id
  policy = data.aws_iam_policy_document.codebuild_policy.json
}
module "disable_access_key_lambda" {
  source = "./modules/lambda"
  lambda_name = var.lambda_name
  
}

resource "aws_sns_topic" "security_alerts" {
  name = "credential-scan-alerts-bpl"
}
resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.security_alerts.arn
  protocol  = "email"
  endpoint  = "bidyut.pal@edifixio.com"
}
resource "aws_sagemaker_model" "scanner" {
  name               = "credential-scanner-model-v1"
  execution_role_arn = var.sagemaker_execution_role

  primary_container {
    image          = var.sklearn_image_uri
    model_data_url = var.model_artifact_s3
    environment = {
      SAGEMAKER_PROGRAM = "inference.py"
      SAGEMAKER_SUBMIT_DIRECTORY = var.inference_source_s3
    }
  }
}

resource "aws_sagemaker_endpoint_configuration" "scanner" {
  name = "credential-scanner-config"

  production_variants {
    model_name             = aws_sagemaker_model.scanner.name
    variant_name           = "AllTraffic"
    instance_type          = "ml.m5.large"
    initial_instance_count = 1
  }
}

resource "aws_sagemaker_endpoint" "scanner" {
  name                 = "credential-scanner-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.scanner.name
}

resource "aws_codebuild_project" "scan" {
  name          = "credential-scan-build"
  service_role = aws_iam_role.codebuild_role.arn

  artifacts { type = "CODEPIPELINE" }

  environment {
    image        = "aws/codebuild/standard:7.0"
    compute_type = "BUILD_GENERAL1_SMALL"
    type         = "LINUX_CONTAINER"

    environment_variable {
      name  = "SAGEMAKER_ENDPOINT_NAME"
      value = "credential-scanner-endpoint"
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "buildspec-scan.yml"
  }
}

resource "aws_codepipeline" "code_scan" {
  name     = "code-scan-pipeline"
  role_arn = "arn:aws:iam::361509912577:role/bpl-training-codepipeline-role"

  artifact_store {
    location = var.artifact_bucket_name
    type     = "S3"
  }

  stage {
        name = "Source"
        action {
          name             = "Source"
          category         = "Source"
          owner            = "AWS"
          provider         = "CodeStarSourceConnection"
          version          = "1"
          output_artifacts = ["source_output"]
          configuration = {
            ConnectionArn    = var.codestar_connection_con
            FullRepositoryId = "gitbidyut/code-scanner-job-bpl" # e.g., "myuser/my-repo"
            #RepositoryName = aws_codecommit_repository.app_repo.repository_name
            BranchName     = "main"
          }
        }
      }

  stage {
    name = "Scan"
    action {
      name            = "ScanCode"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      input_artifacts = ["source_output"]
      version = "1"
      configuration = {
        ProjectName = aws_codebuild_project.scan.name
      }
    }
  }
}