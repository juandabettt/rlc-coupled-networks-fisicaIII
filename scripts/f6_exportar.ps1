# Fase 6: actualiza el indice del informe en Word y lo exporta a PDF.
#
# Usa Microsoft Word (automatizacion COM) sin mostrar la ventana:
#   1. abre docs/informe/Informe_final_red_RLC.docx;
#   2. actualiza el indice y los campos (numeros de pagina);
#   3. guarda el .docx y exporta el .pdf junto a el.
#
# (Sin tildes a proposito: Windows PowerShell 5.1 lee los .ps1 sin BOM como ANSI.)
#
# Uso, desde la raiz del proyecto (PowerShell):
#   powershell -ExecutionPolicy Bypass -File scripts/f6_exportar.ps1

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
$docx = Join-Path $raiz "docs\informe\Informe_final_red_RLC.docx"
$pdf = [System.IO.Path]::ChangeExtension($docx, ".pdf")
if (-not (Test-Path $docx)) { throw "No existe $docx. Corre antes: python scripts/f6_informe.py" }

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($docx)
    foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
    $doc.Fields.Update() | Out-Null
    foreach ($toc in $doc.TablesOfContents) { $toc.UpdatePageNumbers() }
    $doc.Save()
    $doc.ExportAsFixedFormat($pdf, 17)          # 17 = wdExportFormatPDF
    "Paginas: " + $doc.ComputeStatistics(2)     # 2 = wdStatisticPages
    $doc.Close([ref]0)
    "Guardado: $docx"
    "PDF:      $pdf"
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
