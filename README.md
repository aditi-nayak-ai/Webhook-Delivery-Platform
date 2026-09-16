# 🚀 Webhook Delivery Platform

A production-grade **event-driven backend system** built with Django that enables reliable, secure, and scalable webhook delivery to external services.

This system mimics real-world architectures used in platforms like Stripe and GitHub for handling asynchronous event notifications.

---

## 📌 Overview

The Webhook Delivery Platform allows clients to:

- Register webhook endpoints  
- Publish events  
- Deliver payloads to external systems  
- Retry failed deliveries automatically  
- Verify authenticity using HMAC signatures  
- Track delivery status and logs  

---

## 🏗️ Architecture
Client → Django API → Event Creation
↓
PostgreSQL
↓
Redis Queue
↓
Celery Workers
↓
Webhook Delivery 


---

## ⚙️ Tech Stack

### Backend
- Django  
- Django REST Framework  

### Database
- PostgreSQL  

### Async Processing
- Celery  
- Redis  

### Deployment
- Docker  
- Gunicorn  

### Security
- HMAC Signature Verification  
- JWT Authentication  

---

## 📂 Project Structure
webhook_platform/
```
apps/
users/
webhooks/
events/
deliveries/

core/
settings.py
celery.py
utils.py

docker-compose.yml
manage.py
```
---

## 🔑 Core Features

### 1. Webhook Registration

- POST /api/webhooks
---

### 2. Event Publishing

- POST /api/events
---

### 3. Asynchronous Delivery System

- Events are queued using Redis  
- Celery workers process delivery  
- Non-blocking API design  

---

### 4. Retry Mechanism

- Automatic retries on failure  
- Exponential backoff strategy  
- Fault-tolerant system  

---

### 5. Secure Webhooks (HMAC)

Each request includes:


X-Webhook-Signature


Generated using SHA256 to ensure payload integrity.

---

### 6. Delivery Tracking

Track:

- status (pending, success, failed)  
- response codes  
- retry attempts  
- timestamps  

---

## 🧠 System Design Highlights

- Event-driven architecture  
- Decoupled services (API + workers)  
- Scalable background processing  
- Fault tolerance & retry logic  

---

## 🚀 Getting Started

### 1. Clone Repository

```bash
git clone https://github.com/your-username/webhook-platform.git
cd webhook-platform
```
### 2. Run with Docker
```
docker-compose up --build
```
### 3. Apply Migrations
```                                                                                                                                                                                   
docker-compose exec web python manage.py migrate
```
### 4. Create Superuser
```
docker-compose exec web python manage.py createsuperuser
```
### 🔌 API Endpoints
Method	Endpoint	Description
POST	/api/webhooks/	Register webhook
GET	/api/webhooks/	List webhooks
POST	/api/events/	Trigger event
GET	/api/deliveries/	View delivery logs

### 🧪 Testing Example
```
Register Webhook
{
  "url": "https://example.com/webhook",
  "event_type": "payment.success",
  "secret": "mysecret"
}
Trigger Event
{
  "event_type": "payment.success",
  "payload": {
    "amount": 1000,
    "currency": "INR"
  }
}
```

### 📈 Future Enhancements
- Dead Letter Queue (DLQ)
- Webhook retry dashboard
- Rate limiting
- OpenAPI / Swagger docs
- Monitoring & alerting

### Screenshot

<img width="1920" height="1080" alt="Screenshot (386)" src="https://github.com/user-attachments/assets/338c899f-aeb9-48ea-a40c-b706ba21207b" />

<img width="1920" height="1080" alt="Screenshot (391)" src="https://github.com/user-attachments/assets/e58d57a4-0b1f-40b1-b27f-b0a59b8b15ce" />

<img width="1920" height="1080" alt="Screenshot (390)" src="https://github.com/user-attachments/assets/902429c9-8f5a-4207-8c63-6ead97f4f660" />

### 👩‍💻 Author - Aditi Nayak
