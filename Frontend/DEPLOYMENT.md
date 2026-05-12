# Vercel Deployment Guide for Clarimo AI Frontend

This guide will walk you through deploying the Clarimo AI frontend to Vercel.

## Prerequisites

1. A [Vercel account](https://vercel.com/signup) (free tier works fine)
2. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. Your backend API deployed and accessible via HTTPS

## Step 1: Prepare Your Repository

Make sure all your latest changes are committed and pushed to your Git repository:

```bash
git add .
git commit -m "Prepare frontend for Vercel deployment"
git push origin main
```

## Step 2: Import Project to Vercel

### Option A: Using Vercel Dashboard (Recommended)

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Select your Git provider (GitHub, GitLab, or Bitbucket)
4. Authorize Vercel to access your repositories
5. Select the repository containing your frontend code
6. Click **"Import"**

### Option B: Using Vercel CLI

```bash
# Install Vercel CLI globally
npm install -g vercel

# Navigate to your frontend directory
cd Frontend

# Deploy
vercel
```

## Step 3: Configure Build Settings

Vercel should auto-detect your Vite project. Verify these settings:

- **Framework Preset**: Vite
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`
- **Root Directory**: `Frontend` (if deploying from monorepo)

> **Note**: The `vercel.json` file in your project already contains these configurations.

## Step 4: Configure Environment Variables

This is the **most important step**! Add your environment variables in the Vercel dashboard:

1. In your project settings, go to **"Settings"** → **"Environment Variables"**
2. Add the following variable:

| Name | Value | Environment |
|------|-------|-------------|
| `VITE_API_BASE_URL` | `https://your-backend-api.com/api` | Production, Preview, Development |

**Important**: Replace `https://your-backend-api.com/api` with your actual backend API URL.

### Example Values:

- **Production Backend**: `https://api.clarimo.ai/api`
- **Staging Backend**: `https://staging-api.clarimo.ai/api`
- **Local Development**: `http://localhost:8000/api` (already in `.env`)

## Step 5: Deploy

1. Click **"Deploy"** in the Vercel dashboard
2. Wait for the build to complete (usually 1-3 minutes)
3. Once deployed, Vercel will provide you with:
   - **Production URL**: `https://your-project.vercel.app`
   - **Preview URLs**: For each branch/PR

## Step 6: Configure Custom Domain (Optional)

1. Go to **"Settings"** → **"Domains"**
2. Add your custom domain (e.g., `app.clarimo.ai`)
3. Follow Vercel's instructions to update your DNS records
4. Vercel will automatically provision an SSL certificate

## Step 7: Verify Deployment

1. Visit your deployed URL
2. Test the following:
   - ✅ Landing page loads correctly
   - ✅ Logo and favicon appear
   - ✅ Login/Signup works
   - ✅ API calls connect to your backend
   - ✅ All routes work (refresh on any page should work)

## Troubleshooting

### Build Fails

**Error**: `Module not found` or dependency issues

**Solution**: 
```bash
# Locally test the build
cd Frontend
npm install
npm run build
```

### API Calls Fail (CORS Errors)

**Problem**: Backend rejects requests from your Vercel domain

**Solution**: Update your backend CORS settings to allow your Vercel domain:

```python
# Backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://your-project.vercel.app",  # Add this
        "https://app.clarimo.ai",  # Add custom domain if applicable
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Environment Variables Not Working

**Problem**: `VITE_API_BASE_URL` is undefined

**Solution**: 
1. Verify the variable name starts with `VITE_`
2. Redeploy after adding environment variables
3. Check the variable is set for the correct environment (Production/Preview/Development)

### Routes Return 404 on Refresh

**Problem**: Direct navigation to routes like `/dashboard` returns 404

**Solution**: This should be handled by `vercel.json`. Verify the file exists with:

```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

## Continuous Deployment

Vercel automatically deploys:
- **Production**: When you push to `main` branch
- **Preview**: When you create a pull request or push to other branches

To disable auto-deployment:
1. Go to **"Settings"** → **"Git"**
2. Configure deployment branches

## Performance Optimization

Your deployment is already optimized with:
- ✅ Asset caching (31536000 seconds for `/assets/*`)
- ✅ Automatic code splitting (Vite)
- ✅ Minification and compression
- ✅ CDN distribution (Vercel Edge Network)

## Monitoring

Monitor your deployment:
1. **Analytics**: Settings → Analytics (track page views, performance)
2. **Logs**: Deployments → [Select deployment] → View Function Logs
3. **Speed Insights**: Settings → Speed Insights (Core Web Vitals)

## Rollback

If something goes wrong:
1. Go to **"Deployments"**
2. Find a previous working deployment
3. Click **"..."** → **"Promote to Production"**

## Local Development

Your local `.env` file is already configured:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

This allows you to develop locally while production uses the Vercel environment variable.

## Support

- [Vercel Documentation](https://vercel.com/docs)
- [Vite Deployment Guide](https://vitejs.dev/guide/static-deploy.html#vercel)
- [Vercel Community](https://github.com/vercel/vercel/discussions)

---

## Quick Checklist

- [ ] Code pushed to Git repository
- [ ] Project imported to Vercel
- [ ] `VITE_API_BASE_URL` environment variable set
- [ ] Backend CORS configured for Vercel domain
- [ ] Deployment successful
- [ ] Login/Signup tested
- [ ] API calls working
- [ ] All routes accessible
- [ ] Custom domain configured (optional)

---

**Deployment Date**: _____________

**Production URL**: _____________

**Backend API URL**: _____________
