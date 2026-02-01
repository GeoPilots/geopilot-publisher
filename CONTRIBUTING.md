# Contributing to GeoPilots Media Repository

Thank you for your interest in contributing to the GeoPilots Media Repository! This document provides guidelines for contributing media assets.

## 📋 Before You Contribute

- Ensure you have the legal rights to share the media you're uploading
- Verify that the media doesn't contain sensitive or proprietary information
- Check if similar media already exists in the repository to avoid duplicates

## 🎯 Contribution Process

### 1. Set Up Your Environment

```bash
# Clone the repository
git clone https://github.com/GeoPilots/geopilot-publisher.git
cd geopilot-publisher

# Install Git LFS if you haven't already
git lfs install

# Create a new branch
git checkout -b add-new-media
```

### 2. Add Your Media

- Place files in the appropriate `assets/` subdirectory
- Follow the naming conventions (lowercase, hyphens, descriptive)
- Optimize files before adding them (see optimization guidelines below)

### 3. Commit Your Changes

```bash
# Stage your files
git add assets/images/my-new-image.png

# Commit with a descriptive message
git commit -m "Add hero image for new landing page"

# Push to your branch
git push origin add-new-media
```

### 4. Create a Pull Request

- Go to the repository on GitHub
- Click "New Pull Request"
- Select your branch
- Provide a clear description of what media you're adding and why
- Submit the pull request

## 📐 File Specifications

### Images

| Format | Use Case | Max Size | Recommended Tools |
|--------|----------|----------|-------------------|
| PNG | Logos, icons, UI elements with transparency | 2MB | pngquant, optipng |
| JPG | Photos, complex images without transparency | 1MB | jpegoptim, mozjpeg |
| SVG | Scalable graphics, icons, logos | 100KB | svgo |
| WebP | Modern web images | 1MB | cwebp |

### Videos

| Format | Use Case | Max Size | Recommended Settings |
|--------|----------|----------|----------------------|
| MP4 | General web video | 50MB | H.264, 1080p, 2-5 Mbps |
| WebM | Modern browsers | 50MB | VP9, 1080p |

### Audio

| Format | Use Case | Max Size | Recommended Settings |
|--------|----------|----------|----------------------|
| MP3 | General audio | 10MB | 128-192 kbps |
| WAV | High-quality source | 50MB | Uncompressed |

## 🛠️ Optimization Tools

### Command-line Tools

```bash
# Optimize PNG
pngquant image.png --output image-optimized.png

# Optimize JPG
jpegoptim --max=85 image.jpg

# Optimize SVG
svgo image.svg

# Convert to WebP
cwebp -q 80 image.png -o image.webp

# Compress video
ffmpeg -i input.mp4 -vcodec h264 -acodec aac -crf 23 output.mp4
```

### Online Tools

- **Images**: [TinyPNG](https://tinypng.com/), [Squoosh](https://squoosh.app/)
- **Videos**: [HandBrake](https://handbrake.fr/)
- **SVG**: [SVGOMG](https://jakearchibald.github.io/svgomg/)

## ✅ Quality Checklist

Before submitting your contribution, ensure:

- [ ] Files are in the correct directory
- [ ] Filenames follow the naming convention
- [ ] Files are optimized and under size limits
- [ ] No sensitive information is included
- [ ] You have the rights to share the media
- [ ] Similar files don't already exist
- [ ] Commit message is descriptive
- [ ] Pull request includes context about the media

## 🚫 What Not to Upload

- Personal or sensitive information
- Copyrighted material without permission
- Extremely large files (>50MB for videos, >5MB for images)
- Redundant or duplicate files
- Unoptimized media files

## 🔍 Review Process

1. A maintainer will review your pull request
2. They may request changes or optimizations
3. Once approved, your media will be merged
4. Your contribution will be available to all GeoPilots projects

## 💡 Tips

- **Start small**: Begin with one or two files to familiarize yourself with the process
- **Ask questions**: Open an issue if you're unsure about anything
- **Be descriptive**: Good commit messages and PR descriptions help reviewers
- **Test locally**: Verify that LFS is working correctly before pushing

## 📞 Getting Help

If you have questions or need assistance:

1. Check the [README](README.md) for basic information
2. Open an issue for general questions
3. Reach out to the maintainers

Thank you for contributing to GeoPilots! 🎉
