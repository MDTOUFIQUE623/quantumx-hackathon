# Vendored browser dependencies

`liboqs-js` is copied here so WASM modules load from the same origin as the app (CDN bundlers break WASM).

Refresh after upgrading:

```bash
cd static/vendor
npm install @oqs/liboqs-js@0.15.1
rm -rf liboqs-js
cp -r node_modules/@oqs/liboqs-js ./liboqs-js
```

On Windows (PowerShell):

```powershell
cd static/vendor
npm install @oqs/liboqs-js@0.15.1
Remove-Item -Recurse -Force liboqs-js -ErrorAction SilentlyContinue
Copy-Item -Recurse node_modules/@oqs/liboqs-js liboqs-js
```
