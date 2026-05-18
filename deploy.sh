#!/bin/bash
# 🌐 Sahel Dev - Deploy to Vercel Script

echo "🚀 Deploying Sahel Dev Landing Page to Vercel..."
echo ""

# Check if vercel is installed
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
fi

# Navigate to project
cd /home/ubuntu/sahel_dev

# Deploy to Vercel
echo "📤 Uploading to Vercel..."
vercel --prod --yes

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Your landing page is now live!"
echo ""
echo "📋 Next steps:"
echo "1. Set up custom domain: vercel domains add saheldev.com"
echo "2. Configure environment variables"
echo "3. Deploy backend: cd backend && vercel --prod"