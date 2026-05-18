# 🔐 Cloud-Native Secure Document Vault

A reverse-engineered AWS S3-compatible architecture built to demonstrate advanced cloud infrastructure patterns, including **Split-Horizon DNS**, **Pre-signed URL cryptography**, and **Application-Level Role-Based Access Control (RBAC)**.

This project bypasses standard backend anti-patterns by utilizing a dedicated internal DNS resolver to unify internal microservice traffic and external browser requests, perfectly mimicking AWS VPC routing mechanics.

## 🏗️ Architecture & Tech Stack

*   **Compute / API Layer:** Python (FastAPI)
*   **Object Storage:** MinIO (S3-Compatible Storage Engine)
*   **Networking / DNS:** CoreDNS (Mimicking AWS Route 53 Private Hosted Zones)
*   **Orchestration:** Docker Compose
*   **SDK:** `boto3` (AWS SDK for Python)

### The Split-Horizon DNS Design
To solve the `SignatureDoesNotMatch` cryptographic error inherent in AWS Signature Version 4 (SigV4) when operating across Docker boundaries, this project implements a Split-Horizon DNS architecture:
1.  **Inside the VPC:** CoreDNS intercepts FastAPI requests for `vault.local` and routes them to the internal MinIO container IP.
2.  **Outside the VPC:** The host OS resolves `vault.local` to the exposed localhost port.
*Result: Both the backend signature generation and frontend URL resolution utilize the exact same host string, validating the cryptographic hash securely without duplicate clients.*

## ✨ Key Features
*   **Cryptographic Pre-Signed URLs:** Time-limited (60s) secure download links generated via `boto3`.
*   **Data Tagging:** Immutable classification metadata attached directly to objects at the storage layer.
*   **Zero-Trust RBAC:** Intercept middleware that mathematically evaluates user clearance against storage metadata tags before generating access tokens.
*   **Twelve-Factor Compliant:** Complete separation of configuration and code via `.env`.

---

## 🚀 Quick Start Guide

### Prerequisites
*   Docker & Docker Compose
*   Linux/Debian environment (recommended)

### 1. Configure the Host OS Resolver
To allow your local browser to access the unified DNS endpoint, append the domain to your local hosts file.

`sudo nano /etc/hosts`

Add the following line to the bottom:
`127.0.0.1    vault.local`

### 2. Clone and Configure
`git clone https://github.com/django-frog/s3-replica-architecture.git`
`cd s3-replica-architecture`

Ensure your `.env` file matches the unified endpoint:
```env
APP_ENV=development
MINIO_ENDPOINT=vault.local:9000
MINIO_ACCESS_KEY=root_admin
MINIO_SECRET_KEY=secure_password_123
MINIO_BUCKET_NAME=secure-vault
URL_EXPIRATION=60

```

### 3. Deploy the Cloud Infrastructure

Boot the custom VPC network, CoreDNS server, MinIO cluster, and FastAPI application:
`docker compose up --build -d`

### 4. Test the Vault

1. Open `index.html` in your web browser.
2. Select an **Active User Session** (e.g., Alice - Public Clearance).
3. Upload a file and tag it as **Public**. Click the generated secure link to download.
4. Attempt to upload a file tagged as **Restricted**. The application layer will intercept the request and return an HTTP `403 Forbidden` access denial.

---

## 🗺️ Roadmap: The "Dropbox" Scale

This repository serves as the baseline foundation. Upcoming architectural iterations include:

* [ ] **High Availability:** Deploying an Nginx Reverse Proxy / Application Load Balancer.
* [ ] **Compute Replication:** Scaling the FastAPI service to multiple instances with Round-Robin distribution.
* [ ] **Storage Clustering:** Upgrading MinIO to a 4-node distributed cluster utilizing Erasure Coding for data survivability.
