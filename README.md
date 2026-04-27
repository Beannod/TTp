# TTp - Easy Phone to PC File Transfer

TTp is a simple, user-friendly tool for fast and hassle-free file transfers from your phone to your Windows PC—no USB cables or complicated setup required.

## Features

- 🚀 **Quick Setup:** Start transferring files in seconds with minimal configuration.
- 📱 **Cross-Device Support:** Send photos, videos, and any files from any smartphone (iPhone, Android, or others) or tablet to your PC.
- 🌐 **Web-Based Interface:** Transfer files using any browser—Safari, Chrome, Edge, Firefox, and more.
- 🔒 **Secure & Private:** Direct local network transfer. **Password protection by default:** password is set when you start the server and required for access.
- 🖥️ **Works on Windows:** Designed for Windows PCs. Just double-click to start.
- 📷 **QR Code Convenience:** Scan a QR code with your phone to instantly open the transfer page—no manual typing!
- 🔄 **Stay Updated:** Get notified if a new version is available on GitHub, so you always have the latest features and security fixes.

## How It Works

1. **Start the Server:**
   - Double-click `start.bat` on your Windows PC.
   - The script automatically installs any required Python dependencies.
   - When TTp starts, you will be prompted to **set a password** for the session. This password protects the web page for file uploads.
   - TTp checks if a new update is available on GitHub and lets you know if an update exists.
   - After setup, TTp displays a local address (e.g., `http://192.168.x.x:8080`) **and a QR code**.

2. **Connect Your Phone:**
   - Make sure your phone or tablet is on the same Wi-Fi network as your PC.
   - Open your camera or any QR code scanner on your device and scan the QR code shown by TTp.
   - This will open the transfer web page in your phone’s browser.

3. **Login & Transfer Files:**
   - When prompted, enter the **password** you set at server startup.
   - Select files to transfer—your files will appear on your PC right away!

## Security

- **Password Protection:** Every session is protected by a password you set when starting the server. Only people with the password on the same network can access the transfer page.
- **Local-Only Transfers:** TTp never uploads files to the cloud or external services; all transfers stay on your network.

## Keeping TTp Up-to-Date

- On startup, TTp will automatically check for updates on GitHub.
- If a new version is available, you will be notified and given a link to download the latest release.
- You can always visit [the TTp GitHub repository](https://github.com/Beannod/TTp) to manually check for the latest version.

## Requirements

- Windows PC.
- Phone or tablet on the same Wi-Fi network as your PC.
- Modern web browser (Safari, Chrome, Edge, Firefox, Opera, etc).

## Getting Started

1. **Clone the Repo:**
    ```sh
    git clone https://github.com/Beannod/TTp.git
    cd TTp
    ```

2. **Start TTp:**
   - Double-click `start.bat`.
   - Set a secure password when prompted.

3. **Transfer Files:**
   - Scan the QR code with your phone (or enter the provided address manually).
   - Enter the password.
   - Upload your files—instant transfer to your PC!

## Why TTp?

- No cables, no special apps—just scan and go.
- Password-protected, secure local transfers.
- Works with all major smartphones and tablets.
- Lightning-fast, private transfers on your own Wi-Fi.
- Easy update notifications keep you current.

## License

MIT License

---

Enjoy easy, secure, and fast file transfer from your phone to your PC with TTp!
