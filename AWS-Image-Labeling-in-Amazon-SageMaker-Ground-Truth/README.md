# 🏷️ Image Labeling in Amazon SageMaker Ground Truth
 
A hands-on lab project demonstrating how to build high-quality labeled image datasets using **Amazon SageMaker Ground Truth** — the foundation of every successful computer vision model.
 
---
 
## 📖 Overview
 
This project walks through the end-to-end process of setting up an **Image Classification Labeling Job** on AWS using SageMaker Ground Truth. It covers everything from S3 bucket configuration and image upload, to workforce setup and launching a fully managed annotation workflow.
 
> **"Every great AI model starts with great data."**  
> Investing in data labeling and quality assurance is the most critical — and often most overlooked — stage of machine learning development.
 
---
 
## 🚀 What is Amazon SageMaker Ground Truth?
 
**Amazon SageMaker Ground Truth** is a fully managed data labeling service that combines **human annotation** with **automated machine learning** to efficiently create high-quality training datasets for images, text, and video.
 
### Key Features
 
| Feature | Description |
|---|---|
| **Labeling Tasks** | Image classification, bounding box, semantic segmentation, text classification |
| **Workforce Management** | Private workforce (internal teams) or public workforce via Amazon Mechanical Turk |
| **Automated Labeling** | ML-assisted pre-labeling to reduce manual effort and cost |
| **Quality Control** | Built-in review mechanisms to ensure labeled data accuracy |
 
---
 
## 🎯 Lab Objectives
 
By the end of this lab, you will be able to:
 
- ✅ Create and configure an **Amazon S3 bucket** for storing image datasets
- ✅ Upload image data to AWS for annotation workflows
- ✅ Set up a **private workforce** for labeling tasks
- ✅ Configure and launch an **Image Classification Labeling Job**
- ✅ Prepare labeled datasets ready for training computer vision models
---
 
## 🛠️ Technologies Used
 
- **Amazon SageMaker Ground Truth** — Managed data labeling service
- **Amazon S3** — Object storage for image datasets
- **AWS IAM / Workforce Management** — Identity and access control for labeling teams
- **Image Classification Labeling Workflows** — SageMaker built-in task type
- **Data Annotation & Dataset Preparation** — End-to-end ML data pipeline
---
 
## 🗂️ Lab Steps
 
### 1. Create an S3 Bucket
Create a dedicated S3 bucket to store your image dataset that will be used for the labeling job.
 
```
Bucket ARN: arn:aws:s3:::m21academyturk
```
 
### 2. Upload Image Data
Upload your image files to the S3 bucket. Once uploaded, they are ready to be consumed by SageMaker Ground Truth or any other AWS service.
 
### 3. Set Up a Private Workforce
Configure a private workforce of labelers using AWS workforce management. This allows you to use internal team members for annotation tasks with access control.
 
### 4. Create a Labeling Job
Navigate to **SageMaker Ground Truth** in the AWS Console and configure a new labeling job:
- Select **Image Classification** as the task type
- Point the job to your S3 bucket as the data source
- Assign the job to your private workforce
- Define label categories
### 5. Start Labeling
Launch the labeling job. Workforce members access the labeling UI, classify images, and submit annotations. SageMaker's automated labeling can assist by pre-labeling high-confidence samples.
 
### 6. Export Labeled Dataset
Once complete, the output manifest file is saved back to S3 and is ready to be used as a training dataset for computer vision models.
 
---
 
## 💡 Key Learnings
 
- How SageMaker Ground Truth streamlines the **data annotation lifecycle** for ML projects
- The importance of **workforce management** and quality control in data labeling
- How **human-in-the-loop** and automated labeling approaches improve efficiency and reduce cost
- Best practices for building reliable, production-ready datasets for image classification
---
 
## 📌 Prerequisites
 
- An active **AWS account** with appropriate IAM permissions
- Basic familiarity with the **AWS Management Console**
- Images ready for annotation (JPEG/PNG format recommended)
---
 
## 📚 Resources
 
- [Amazon SageMaker Ground Truth Documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/sms.html)
- [Amazon S3 Documentation](https://docs.aws.amazon.com/s3/)
- [SageMaker Ground Truth Pricing](https://aws.amazon.com/sagemaker/groundtruth/pricing/)
---
 
## 🏷️ Tags
 
`AWS` `SageMaker` `GroundTruth` `MachineLearning` `ComputerVision` `DataAnnotation` `ImageClassification` `MLOps` `DataScience` `CloudComputing`
 


