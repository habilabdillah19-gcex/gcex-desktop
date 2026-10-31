; Installer DB-Ex (Qt for Python / PySide6). Dibangun CI:
;   makensis /DVERSION=1.0.0 /DSRC=<folder hasil PyInstaller> /DOUT=<file .exe> /DROOT=<akar repo> tools\corex_qt\installer.nsi
; Per pengguna (tanpa hak admin), folder bisa diubah, halaman Syarat Penggunaan, pintasan Desktop & Start Menu.
; Versi lama di-uninstall diam-diam dulu: Electron (Core-Ex / DB-Ex) dan Core-Ex Qt (<= 0.30.x, nama lama sebelum DB-Ex);
; lisensi, pengaturan (dipindah otomatis dari %APPDATA%\Core-Ex ke %APPDATA%\DB-Ex saat pertama dibuka) & data proyek tidak tersentuh.
Unicode true
ManifestDPIAware true
SetCompressor /SOLID lzma
RequestExecutionLevel user

!ifndef VERSION
  !define VERSION "0.0.0"
!endif
!define APP "DB-Ex"
!define EXE "DB-Ex.exe"
!define UKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\DB-Ex-Qt"

Name "${APP} ${VERSION}"
OutFile "${OUT}"
InstallDir "$LOCALAPPDATA\Programs\DB-Ex"
InstallDirRegKey HKCU "${UKEY}" "InstallLocation"
BrandingText "DB-Ex ${VERSION} - keluarga GC-Ex"
VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "DB-Ex"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "FileDescription" "DB-Ex (Database Excellence) installer"
VIAddVersionKey "LegalCopyright" "Copyright (c) 2026 Habil Abdillah"
VIAddVersionKey "LegalTrademarks" "DB-Ex, Database Excellence dan GC-Ex adalah nama produk milik Habil Abdillah"

!include "MUI2.nsh"
!include "LogicLib.nsh"
!define MUI_ICON "${ROOT}\build\icon-core.ico"
!define MUI_UNICON "${ROOT}\build\icon-core.ico"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\${EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Jalankan DB-Ex"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${ROOT}\legal\SYARAT_PENGGUNAAN.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Indonesian"

; ---- copot versi lama: Electron (kunci ber-GUID, DisplayName "Core-Ex <versi>" / "DB-Ex <versi>") dan Core-Ex Qt (kunci "Core-Ex-Qt")
Function RemoveElectron
  StrCpy $0 0
  loop:
    EnumRegKey $1 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall" $0
    StrCmp $1 "" done
    IntOp $0 $0 + 1
    StrCmp $1 "DB-Ex-Qt" loop
    ReadRegStr $2 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$1" "DisplayName"
    StrCpy $3 $2 8
    StrCmp $3 "Core-Ex " found
    StrCpy $3 $2 6
    StrCmp $3 "DB-Ex " found loop
    found:
    ReadRegStr $4 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$1" "QuietUninstallString"
    StrCmp $4 "" loop
    ReadRegStr $6 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\$1" "InstallLocation"
    DetailPrint "Menghapus $2 (versi lama)..."
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

Section "DB-Ex" SecMain
  SectionIn RO
  ; aplikasi yang sedang berjalan ditutup dulu
  nsExec::Exec 'taskkill /F /IM "${EXE}"'
  nsExec::Exec 'taskkill /F /IM "Core-Ex.exe"'
  Call RemoveElectron
  ; pintasan nama lama (bila uninstaller lama tidak menghapusnya)
  Delete "$DESKTOP\Core-Ex.lnk"
  RMDir /r "$SMPROGRAMS\Core-Ex"
  SetOutPath "$INSTDIR"
  RMDir /r "$INSTDIR\_internal"
  File /r "${SRC}\*.*"
  WriteUninstaller "$INSTDIR\Uninstall DB-Ex.exe"
  CreateShortcut "$DESKTOP\DB-Ex.lnk" "$INSTDIR\${EXE}" "" "$INSTDIR\${EXE}" 0
  CreateDirectory "$SMPROGRAMS\DB-Ex"
  CreateShortcut "$SMPROGRAMS\DB-Ex\DB-Ex.lnk" "$INSTDIR\${EXE}" "" "$INSTDIR\${EXE}" 0
  CreateShortcut "$SMPROGRAMS\DB-Ex\Panduan DB-Ex.lnk" "$INSTDIR\docs\PANDUAN_CORE.html"
  CreateShortcut "$SMPROGRAMS\DB-Ex\Uninstall DB-Ex.lnk" "$INSTDIR\Uninstall DB-Ex.exe"
  WriteRegStr HKCU "${UKEY}" "DisplayName" "DB-Ex ${VERSION}"
  WriteRegStr HKCU "${UKEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${UKEY}" "Publisher" "Habil Abdillah"
  WriteRegStr HKCU "${UKEY}" "DisplayIcon" "$INSTDIR\${EXE}"
  WriteRegStr HKCU "${UKEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UKEY}" "UninstallString" '"$INSTDIR\Uninstall DB-Ex.exe"'
  WriteRegStr HKCU "${UKEY}" "QuietUninstallString" '"$INSTDIR\Uninstall DB-Ex.exe" /S'
  WriteRegDWORD HKCU "${UKEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UKEY}" "NoRepair" 1
SectionEnd

Section "Uninstall"
  nsExec::Exec 'taskkill /F /IM "${EXE}"'
  Delete "$DESKTOP\DB-Ex.lnk"
  RMDir /r "$SMPROGRAMS\DB-Ex"
  RMDir /r "$INSTDIR\_internal"
  RMDir /r "$INSTDIR\legal"
  RMDir /r "$INSTDIR\docs"
  Delete "$INSTDIR\${EXE}"
  Delete "$INSTDIR\Uninstall DB-Ex.exe"
  RMDir "$INSTDIR"
  DeleteRegKey HKCU "${UKEY}"
  ; lisensi (%APPDATA%\GC-Ex Lisensi), pengaturan (%APPDATA%\DB-Ex) dan folder _GCEx_Core di folder foto tidak dihapus
SectionEnd
