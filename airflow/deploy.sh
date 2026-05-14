#!/bin/bash
# Stock Forecast Platform - AWS 배포 스크립트
# 사용법: ./airflow/deploy.sh

set -e

AWS_REGION="eu-west-1"
AWS_ACCOUNT_ID="197840067661"
ECR_REPO="stock-forecast"
S3_DAG_BUCKET="mwaa-bucket-only"
MWAA_DAG_PATH="dags"

echo "============================================================"
echo "  Stock Forecast Platform - AWS Deployment"
echo "============================================================"

# 1. ECR 로그인
echo "[1/5] Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# 2. ECR 리포지토리 생성 (없으면)
echo "[2/5] Creating ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPO --region $AWS_REGION 2>/dev/null || \
    aws ecr create-repository --repository-name $ECR_REPO --region $AWS_REGION

# 3. Docker 이미지 빌드 및 푸시
echo "[3/5] Building and pushing Docker image..."
docker build -t $ECR_REPO -f airflow/docker/Dockerfile .
docker tag $ECR_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

# 4. DAG 파일을 S3에 업로드
echo "[4/5] Uploading DAG to S3..."
aws s3 cp airflow/dags/stock_forecast_dag.py s3://$S3_DAG_BUCKET/$MWAA_DAG_PATH/stock_forecast_dag.py --region $AWS_REGION

# 5. ECS Task Definition 등록
echo "[5/5] Registering ECS Task Definition..."
aws ecs register-task-definition \
    --cli-input-json file://airflow/docker/task-definition.json \
    --region $AWS_REGION

echo ""
echo "============================================================"
echo "  Deployment Complete!"
echo ""
echo "  Next steps:"
echo "  1. Create ECS Cluster: stock-forecast-cluster"
echo "  2. Create IAM roles: ecsTaskExecutionRole, stock-forecast-task-role"
echo "  3. Create RDS PostgreSQL instance"
echo "  4. Create S3 bucket: stock-forecast-reports-$AWS_ACCOUNT_ID"
echo "  5. Update task-definition.json with correct RDS endpoint"
echo "  6. Verify DAG appears in MWAA Airflow UI"
echo "============================================================"
