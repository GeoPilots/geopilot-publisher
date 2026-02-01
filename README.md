# GeoPilots Media Repository

Welcome to the GeoPilots Media Repository! This repository serves as a centralized location for storing and managing all media assets used across GeoPilots projects.

## 📁 Repository Structure

```
geopilot-publisher/
├── assets/
│   ├── images/          # Image files (PNG, JPG, GIF, SVG, WebP)
│   ├── videos/          # Video files (MP4, WebM, MOV, AVI)
│   ├── audio/           # Audio files (MP3, WAV, OGG, FLAC)
│   ├── documents/       # Documents (PDF, PSD, AI)
│   ├── logos/           # Logo variations and brand assets
│   ├── screenshots/     # Application screenshots
│   └── icons/           # Icon assets
├── .gitattributes       # Git LFS configuration
├── .gitignore          # Ignored files and directories
├── LICENSE             # Repository license
└── README.md           # This file
```

## 🚀 Getting Started

### Prerequisites

To work with this repository, you need:

- **Git**: Version 2.0 or higher
- **Git LFS**: For handling large media files

### Installing Git LFS

If you don't have Git LFS installed, follow these steps:

#### macOS
```bash
brew install git-lfs
git lfs install
```

#### Ubuntu/Debian
```bash
sudo apt-get install git-lfs
git lfs install
```

#### Windows
Download and install from [git-lfs.github.com](https://git-lfs.github.com/)

### Cloning the Repository

```bash
git clone https://github.com/GeoPilots/geopilot-publisher.git
cd geopilot-publisher
```

Git LFS will automatically download the media files when you clone or pull.

## 📝 Usage Guidelines

### Adding Media Files

1. **Place files in the appropriate directory** based on their type
2. **Use descriptive filenames** that clearly indicate the content
3. **Optimize files** before uploading to minimize repository size
4. **Commit and push** as you would with regular files

Example:
```bash
# Add your media file to the appropriate directory
cp ~/my-image.png assets/images/

# Stage and commit
git add assets/images/my-image.png
git commit -m "Add new image for landing page"

# Push to remote
git push
```

### File Naming Conventions

- Use lowercase with hyphens: `user-profile-icon.png`
- Include dimensions for raster images: `logo-512x512.png`
- Use descriptive names: `dashboard-overview-screenshot.png`
- Avoid special characters and spaces

### Optimization Guidelines

Before uploading media files, please optimize them:

#### Images
- **PNG**: Use tools like `pngquant` or `optipng`
- **JPG**: Use tools like `jpegoptim` or `mozjpeg`
- **SVG**: Minify with `svgo`

#### Videos
- Use H.264 codec for MP4 files
- Target bitrate: 1-5 Mbps for web video
- Resolution: 1920x1080 or lower for most use cases

#### Audio
- Use MP3 format with 128-192 kbps bitrate for general use
- Use WAV only for source/master files

## 🔒 Git LFS

This repository uses Git LFS to efficiently handle large media files. The following file types are tracked with Git LFS:

- **Images**: `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp`, `.ico`
- **Videos**: `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`
- **Audio**: `.mp3`, `.wav`, `.ogg`, `.flac`, `.aac`
- **Documents**: `.pdf`, `.psd`, `.ai`
- **Archives**: `.zip`, `.tar`, `.gz`, `.rar`, `.7z`

### Checking LFS Status

```bash
# See which files are tracked by LFS
git lfs ls-files

# Check LFS status
git lfs status
```

## 🤝 Contributing

1. Create a feature branch for your changes
2. Add your media files to the appropriate directory
3. Follow the naming conventions and optimization guidelines
4. Commit with a descriptive message
5. Push your branch and create a pull request

## 📄 License

This repository is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- [geopilots-playwright-mcp](https://github.com/GeoPilots/geopilots-playwright-mcp) - Playwright MCP server for GeoPilots

## 📧 Contact

For questions or issues, please open an issue in this repository.

---

**Note**: Always ensure you have the rights to upload and share any media files you add to this repository.