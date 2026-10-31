; Installer Core-Ex (Qt for Python / PySide6). Dibangun CI:
;   makensis /DVERSION=1.0.0 /DSRC=<folder hasil PyInstaller> /DOUT=<file .exe> /DROOT=<akar repo> tools\corex_qt\installer.nsi
; Per pengguna (tanpa hak admin), folder bisa diubah, halaman Syarat Penggunaan, pintasan Desktop & Start Menu.
; Versi Electron lama (Core-Ex <= 0.23.x) di-uninstall diam-diam dulu; lisensi, pengaturan & data proyek tidak tersentuh.
Unicode true
ManifestDPIAware true
SetCompressor /SOLID lzma
RequestExecutionLevel user

!ifndef VERSION
  !define VERSION "0.0.0"
!endif
!define APP "Core-Ex"
!define EXE "Core-Ex.exe"
!define UKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\Core-Ex-Qt"

Name "${APP} ${VERSION}"
OutFile "${OUT}"
InstallDir "$LOCALAPPDATA\Programs\Core-Ex"
InstallDirRegKey HKCU "${UKEY}" "InstallLocation"
BrandingText "Core-Ex ${VERSION} - keluarga GC-Ex"
VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "Core-Ex"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "FileDescription" "Core-Ex (Core Excellence) installer"
VIAddVersionKey "LegalCopyright" "Copyright (c) 2026 Habil Abdillah"
VIAddVersionKey "LegalTrademarks" "Core-Ex, Core Excellence dan GC-Ex adalah nama produk milik Habil Abdillah"

!include "MUI2.nsh"
!include "LogicLib.nsh"
!define MUI_ICON "${ROOT}\build\icon-core.ico"
!define MUI_UNICON "${ROOT}\build\icon-core.ico"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\${EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Jalankan Core-Ex"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${ROOT}\legal\SYARAT_PENGGUNAAN.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Indonesian"

; ---- copot Core-Ex versi Electron (electron-builder: kunci uninstall ber-GUID, DisplayName "Core-Ex <versi>")
Function RemoveElectron
  StrCpy $0 0
  loop:
    EnumRegKey $1 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall" $0
    StrCmp $1 "" done
    IntOp $0 $0 + 1
    StrCmp $1 "Core-Ex-Qt" loop
    ReadRegStr $2 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$1" "DisplayName"
    StrCpy $3 $2 8
    StrCmp $3 "Core-Ex " 0 loop
    ReadRegStr $4 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$1" "QuietUninstallString"
    StrCmp $4 "" loop
    ReadRegStr $6 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$1" "InstallLocation"
    DetailPrint "Menghapus $2 (versi Electron)..."
    ExecWait '$4' $5
    ; uninstaller NSIS menyalin dirinya ke TEMP lalu kembali: tunggu sampai file Electron benar-benar terhapus (maks. 60 detik)
    StrCpy $7 0
    wait:
      StrCmp $6 "" waited
      IfFileExists "$6\resources\app.asar" 0 waited
      IntOp $7 $7 + 1
      IntCmp $7 120 waited
      Sleep 500
      Goto wait
    waited:
    Sleep 500
    StrCpy $0 0
    Goto loop
  done:
FunctionEnd

Section "Core-Ex" SecMain
  SectionIn RO
  ; aplikasi yang sedang berjalan ditutup dulu
  nsExec::Exec 'taskkill /F /IM "${EXE}"'
  Call RemoveElectron
  SetOutPath "$INSTDIR"
  RMDir /r "$INSTDIR\_internal"
  File /r "${SRC}\*.*"
  WriteUninstaller "$INSTDIR\Uninstall Core-Ex.exe"
  CreateShortcut "$DESKTOP\Core-Ex.lnk" "$INSTDIR\${EXE}" "" "$INSTDIR\${EXE}" 0
  CreateDirectory "$SMPROGRAMS\Core-Ex"
  CreateShortcut "$SMPROGRAMS\Core-Ex\Core-Ex.lnk" "$INSTDIR\${EXE}" "" "$INSTDIR\${EXE}" 0
  CreateShortcut "$SMPROGRAMS\Core-Ex\Panduan Core-Ex.lnk" "$INSTDIR\docs\PANDUAN_CORE.html"
  CreateShortcut "$SMPROGRAMS\Core-Ex\Uninstall Core-Ex.lnk" "$INSTDIR\Uninstall Core-Ex.exe"
  WriteRegStr HKCU "${UKEY}" "DisplayName" "Core-Ex ${VERSION}"
  WriteRegStr HKCU "${UKEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${UKEY}" "Publisher" "Habil Abdillah"
  WriteRegStr HKCU "${UKEY}" "DisplayIcon" "$INSTDIR\${EXE}"
  WriteRegStr HKCU "${UKEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UKEY}" "UninstallString" '"$INSTDIR\Uninstall Core-Ex.exe"'
  WriteRegStr HKCU "${UKEY}" "QuietUninstallString" '"$INSTDIR\Uninstall Core-Ex.exe" /S'
  WriteRegDWORD HKCU "${UKEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UKEY}" "NoRepair" 1
SectionEnd

Section "Uninstall"
  nsExec::Exec 'taskkill /F /IM "${EXE}"'
  Delete "$DESKTOP\Core-Ex.lnk"
  RMDir /r "$SMPROGRAMS\Core-Ex"
  RMDir /r "$INSTDIR\_internal"
  RMDir /r "$INSTDIR\legal"
  RMDir /r "$INSTDIR\docs"
  Delete "$INSTDIR\${EXE}"
  Delete "$INSTDIR\Uninstall Core-Ex.exe"
  RMDir "$INSTDIR"
  DeleteRegKey HKCU "${UKEY}"
  ; lisensi (%APPDATA%\GC-Ex Lisensi), pengaturan (%APPDATA%\Core-Ex) dan folder _GCEx_Core di folder foto tidak dihapus
SectionEnd
