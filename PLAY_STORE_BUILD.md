# TASVIA Academy — Play Store build

The Android package is configured as a Trusted Web Activity for:

https://apk.tasviaacademy.com/

Package ID:

com.tasviaacademy.app

## Build

The GitHub Actions workflow `.github/workflows/build-tasvia-android.yml` builds a signed APK and Android App Bundle (AAB).

Before running it, add these GitHub Actions secrets:

- `TASVIA_KEYSTORE_BASE64` — base64 contents of the private upload keystore
- `TASVIA_KEYSTORE_PASSWORD` — keystore password
- `TASVIA_KEY_PASSWORD` — key password

Never commit the keystore or passwords to the repository.

## Digital Asset Links

After the first Play Console release, use the **Play App Signing certificate SHA-256** from Play Console to generate the final `/.well-known/assetlinks.json`. The upload-key fingerprint is not necessarily the certificate users receive from Google Play.

The app targets Android API 36 through the current Bubblewrap Android template.
