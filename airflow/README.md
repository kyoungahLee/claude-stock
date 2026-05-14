# MWAA (Airflow) 배포 가이드

## 아키텍처

```
MWAA (Airflow DAG)
  │
  ├── 08:00 KST: KR 전망 리포트 → ECS Fargate Task
  ├── 16:00 KST: KR 마감 리포트 + 백테스트 → ECS Fargate Task
  ├── 22:00 KST: US 전망 리포트 → ECS Fargate Task
  └── 06:30 KST: US 마감 리포트 + 백테스트 → ECS Fargate Task
                    │
                    ├── Bedrock (Claude Sonnet 4.5) - LLM 분석
                    ├── S3 - 리포트 저장
                    ├── RDS PostgreSQL - 예측/결과 DB
                    └── CloudWatch Logs - 실행 로그
```

## 환경 정보

| 항목 | 값 |
|------|-----|
| MWAA 환경 | StockDaily |
| 리전 | eu-west-1 |
| VPC | vpc-09b11676a0e2c3ee1 |
| 서브넷 | subnet-09fd7a476c383a8cd, subnet-0c591e884b7fd1411 |
| 보안 그룹 | sg-09b8deb50bba429d2 |
| S3 DAG 버킷 | s3://mwaa-bucket-only/dags/ |
| AWS 계정 | 197840067661 |

## 배포 순서

### 1. 사전 준비 (1회만)

```bash
# ECS 클러스터 생성
aws ecs create-cluster --cluster-name stock-forecast-cluster --region eu-west-1

# ECR 리포지토리 생성
aws ecr create-repository --repository-name stock-forecast --region eu-west-1

# S3 리포트 버킷 생성
aws s3 mb s3://stock-forecast-reports-197840067661 --region eu-west-1

# CloudWatch 로그 그룹 생성
aws logs create-log-group --log-group-name /ecs/stock-forecast --region eu-west-1

# IAM 역할 생성 (stock-forecast-task-role)
aws iam create-role --role-name stock-forecast-task-role \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}'

aws iam put-role-policy --role-name stock-forecast-task-role \
    --policy-name StockForecastPolicy \
    --policy-document file://airflow/iam-policy-task-role.json
```

### 2. Docker 이미지 빌드 및 배포

```bash
./airflow/deploy.sh
```

### 3. DAG 업로드 확인

DAG 파일이 S3에 업로드되면 MWAA Airflow UI에서 확인:
- `stock_forecast_kr_morning` (08:00 KST)
- `stock_forecast_kr_closing` (16:00 KST)
- `stock_forecast_us_morning` (22:00 KST)
- `stock_forecast_us_closing` (06:30 KST)

### 4. DAG 활성화

Airflow UI에서 각 DAG의 토글을 ON으로 변경.

## 스케줄 요약

| DAG | UTC | KST | 설명 |
|-----|-----|-----|------|
| stock_forecast_kr_morning | 23:00 (전날) | 08:00 | 한국 전망 |
| stock_forecast_kr_closing | 07:00 | 16:00 | 한국 마감 + 백테스트 |
| stock_forecast_us_morning | 13:00 | 22:00 | 미국 전망 |
| stock_forecast_us_closing | 21:30 | 06:30 | 미국 마감 + 백테스트 |

## 비용 예상 (월)

| 서비스 | 예상 비용 |
|--------|----------|
| MWAA (mw1.small) | ~$300 |
| ECS Fargate (하루 4회 × 15분) | ~$5 |
| RDS (db.t3.micro) | ~$15 |
| Bedrock (Claude Sonnet 4.5) | ~$20-30 |
| S3 + CloudWatch | ~$1 |
| **합계** | **~$340-350/월** |
