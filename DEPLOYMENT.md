# UK MPA Analysis App - Coolify Deployment Guide

## 🚀 Deployment to ukmpas.zmescience.com

This guide shows how to deploy the UK MPA Fishing Activity Analysis app using Coolify on your Hetzner server.

## 📋 Prerequisites

- [x] Hetzner server with Ubuntu 22.04.2 LTS
- [x] Coolify installed and running
- [x] Docker installed on server
- [x] Access to zmescience.com DNS management
- [x] GitHub account for code repository

## 🔧 Step 1: Code Repository Setup

### 1.1 Create GitHub Repository
1. Go to GitHub and create a new repository: `uk-mpa-analysis`
2. **CRITICAL**: Copy both folders to your repository:
   ```bash
   # From your local machine:
   cp -r /mnt/d/EJSN\ 2025\ grant/GFW-Extract/mpa_app/* /path/to/uk-mpa-analysis/
   cp -r /mnt/d/EJSN\ 2025\ grant/GFW-Extract/data /path/to/uk-mpa-analysis/
   ```
3. Verify the repository contains:
   - All app files (app.py, templates, static, etc.)
   - **data/uk_mpas_master.csv** (~27MB file)
   - **data/all_mpas_and_features.csv**
4. Commit and push all files to GitHub

### 1.2 Repository Structure
```
uk-mpa-analysis/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── .dockerignore         # Build optimization
├── DEPLOYMENT.md         # This deployment guide
├── static/              # CSS, JS, images
│   ├── css/style.css
│   ├── js/app.js
│   └── logo-zmescience.png
├── templates/           # HTML templates
│   └── index.html
└── data/               # ⚠️ CRITICAL: MPA data files (REQUIRED)
    ├── uk_mpas_master.csv        # ~275 UK MPAs with WDPA codes
    └── all_mpas_and_features.csv # Protected features data
```

### 1.3 Critical Data Dependencies ⚠️

**IMPORTANT**: The application REQUIRES these data files to function:

1. **`data/uk_mpas_master.csv`** (27MB)
   - Contains 275+ UK Marine Protected Areas
   - Includes WDPA codes, coordinates, areas
   - **Without this file, the app cannot load any MPAs**

2. **`data/all_mpas_and_features.csv`** 
   - Contains protected features for each MPA
   - Used for displaying conservation information
   - **Without this file, protected features won't display**

**Repository Setup**: When creating your GitHub repository, ensure you copy BOTH the `mpa_app/` folder AND the `data/` folder from your local setup.

## 🌐 Step 2: DNS Configuration

### 2.1 Point Domain to Server
1. Access zmescience.com DNS management
2. Add A record:
   - **Name**: `ukmpas`
   - **Type**: `A`
   - **Value**: `[Your Hetzner Server IP]`
   - **TTL**: `300` (5 minutes)
3. Wait for DNS propagation (5-15 minutes)

### 2.2 Verify DNS
```bash
# Check DNS propagation
dig ukmpas.zmescience.com
nslookup ukmpas.zmescience.com
```

## 🐳 Step 3: Coolify Deployment

### 3.1 Access Coolify Dashboard
1. Open browser and go to your Coolify dashboard
2. Usually at: `https://[your-hetzner-ip]:8000` or your Coolify domain

### 3.2 Create New Application
1. Click **"Applications"** in sidebar
2. Click **"+ New Application"**
3. Choose **"Git Repository"** as source

### 3.3 Repository Configuration
- **Repository URL**: `https://github.com/[username]/uk-mpa-analysis`
- **Branch**: `main`
- **Build Pack**: `Docker` (Coolify will detect Dockerfile)
- **Port**: `5000`

### 3.4 Domain Configuration
- **Domain**: `ukmpas.zmescience.com`
- **SSL**: ✅ Enable automatic Let's Encrypt
- **Force HTTPS**: ✅ Enable

### 3.5 Environment Variables (Optional)
Set these in Coolify if needed:
- `FLASK_ENV=production`
- `FLASK_DEBUG=false`

### 3.6 Deploy Application
1. Click **"Deploy"** button
2. Monitor build logs in Coolify dashboard
3. Wait for deployment to complete (~3-5 minutes)

## ✅ Step 4: Verification

### 4.1 Check Application
1. Open `https://ukmpas.zmescience.com`
2. Verify homepage loads correctly
3. Test MPA search functionality
4. Test "Browse All" feature
5. Try analyzing an MPA (e.g., "Dogger Bank")
6. Test CSV and PDF exports

### 4.2 Check SSL Certificate
- Green padlock in browser
- Certificate issued by Let's Encrypt
- Valid for ukmpas.zmescience.com

### 4.3 Performance Check
- Page load time < 3 seconds
- Chart rendering works properly
- Mobile responsiveness

## 🔧 Step 5: Production Monitoring

### 5.1 Coolify Dashboard
- Application status: Running ✅
- Memory usage: Monitor
- CPU usage: Monitor
- Logs: Check for errors

### 5.2 Health Monitoring
Coolify automatically monitors:
- Container health checks
- Application uptime
- SSL certificate expiry
- Automatic restarts on failure

## 🚀 Step 6: Future Updates

### 6.1 Automatic Deployments
1. Make changes to code locally
2. Commit and push to GitHub main branch
3. Coolify automatically detects changes
4. Builds and deploys new version
5. Zero-downtime deployment

### 6.2 Manual Deployment
If needed, trigger manual deployment in Coolify:
1. Go to application in Coolify
2. Click "Deploy" button
3. Monitor build process

## 🛠 Troubleshooting

### Common Issues

#### 1. Build Fails
- Check Dockerfile syntax
- Verify requirements.txt contains all dependencies
- Check build logs in Coolify

#### 2. Application Won't Start
- Check if port 5000 is correctly exposed
- Verify gunicorn is in requirements.txt
- Check application logs in Coolify

#### 3. Domain Not Working
- Verify DNS A record points to correct IP
- Check if Coolify proxy is running
- Ensure domain is correctly set in Coolify

#### 4. SSL Issues
- Wait for Let's Encrypt provision (up to 15 minutes)
- Check domain DNS propagation
- Verify domain accessibility from internet

#### 5. Data File Issues
- **Error**: "Could not find uk_mpas_master.csv"
  - Check if data folder is in GitHub repository
  - Verify Dockerfile copies data files correctly
  - Check container logs for file system structure

- **Error**: "No MPAs found" or empty search
  - Verify uk_mpas_master.csv contains data
  - Check file permissions in container
  - Ensure CSV files are valid format

### Debug Commands
```bash
# Check container status
docker ps

# View application logs
docker logs [container-id]

# Check Coolify proxy
docker logs coolify-proxy

# Test local connectivity
curl -I http://localhost:5000
```

## 📊 Performance Optimization

### Production Settings
- ✅ Debug mode disabled
- ✅ Gunicorn WSGI server (2 workers)
- ✅ Docker multi-stage build
- ✅ Non-root container user
- ✅ Health checks enabled

### Resource Requirements
- **RAM**: 512MB minimum, 1GB recommended
- **CPU**: 1 core sufficient for moderate traffic
- **Storage**: 2GB for app + logs
- **Network**: Minimal bandwidth required

## 🔒 Security Features

### Included Security
- ✅ HTTPS/SSL encryption
- ✅ Non-root container execution
- ✅ Automatic security updates via Coolify
- ✅ Firewall managed by Coolify
- ✅ Let's Encrypt certificate auto-renewal

## 📞 Support

### Application Issues
- Check this documentation
- Review Coolify application logs
- Verify DNS configuration
- Test local Docker build

### Contact Information
- **Application**: ZME Science Team
- **Infrastructure**: Hetzner Server Admin
- **Domain**: DNS Management Team

---

## 🎉 Congratulations!

Your UK MPA Analysis app is now live at **https://ukmpas.zmescience.com**

The app provides comprehensive analysis of fishing activity in UK Marine Protected Areas with:
- Interactive MPA search and browsing
- Harmful fishing activity visualization
- Monthly trends for trawling and dredging
- Professional PDF reports with ZME Science branding
- CSV data exports
- Mobile-responsive design

Enjoy your production deployment! 🚀