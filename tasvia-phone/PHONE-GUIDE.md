# Make the TASVIA Academy APK using only a phone

Everything below works in Chrome on an Android phone. Total time is about 45 minutes, and it's free.
Tip: on the Firebase and GitHub sites, tap ⋮ in Chrome and tick **Desktop site**. The menus are easier to find that way.

First, open this zip in your phone's **Files** app and tap **Extract**.

## Part 1: Firebase (the database), about 20 minutes
1. Open console.firebase.google.com and sign in with tasviaacademy@gmail.com.
2. **Create a project** named `tasvia-academy`. Google Analytics is not needed.
3. **Build → Firestore Database → Create database** → location **asia-south1 (Mumbai)** → production mode.
4. Open the **Rules** tab, delete everything, and paste the whole text of `firestore-rules.txt`. Tap **Publish**.
5. **Build → Authentication → Get started → Email/Password → Enable**.
6. **Authentication → Users → Add user**: add yourself and each teacher (email and password).
7. **Firestore → Data → Start collection** → name it `staff`. For each teacher, add a document whose **Document ID is their email in lowercase**, with any field (for example `name`).
8. **Project settings (gear icon) → Your apps → </> (Web)** → name it `TASVIA`. Copy the 6 values it shows (apiKey, authDomain, projectId, storageBucket, messagingSenderId, appId) and keep that screen open.

## Part 2: GitHub (puts the app online), about 15 minutes
1. Open github.com and sign up for free. Pick a username, for example `tasviaacademy`.
2. Tap **+ → New repository** → name it `tasvia` → **Public** → **Create repository**.
3. Tap **uploading an existing file**. Select **all 8 files** inside the `upload-to-github` folder, then **Commit changes**.
4. Tap `firebase-config.js` → the ✏️ pencil icon. Paste your 6 values between the quotes, then **Commit changes**.
5. **Settings → Pages** → Source: **Deploy from a branch** → Branch: **main**, folder **/ (root)** → **Save**.
6. Wait 2–3 minutes. Your app is now live at:
   `https://YOUR-USERNAME.github.io/tasvia/`
   Open it and sign in to check that it works.
7. Back in Firebase: **Authentication → Settings → Authorized domains → Add domain** → `YOUR-USERNAME.github.io`.

## Part 3: Get the APK, about 10 minutes
1. Open pwabuilder.com and paste your app link from Part 2.
2. Tap **Package for stores → Android → Generate package**.
   - Package ID: `com.tasviaacademy.app`
   - App name: `TASVIA Academy`
3. Download the zip and extract it in the Files app.
4. Tap the **.apk** file to install it. Allow "Install unknown apps" when Android asks.
5. Send the same .apk to your teachers on WhatsApp.
6. **Keep the `signing-key` file and the key info text safe** (email them to yourself). You need them for any future update.

## Notes
- The app code is public on GitHub. That's normal and safe: your data is protected by the Firebase rules, and only people in the `staff` list can see it.
- To change the app later, edit `index.html` on GitHub. The installed app picks up the change automatically.
- iPhone teachers: open the Part 2 link in Safari → Share → **Add to Home Screen**.
