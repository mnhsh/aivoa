import * as pdfjsLib from 'pdfjs-dist'

// Set worker source for pdfjs-dist
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`

/**
 * Extract text from all pages of a PDF file asynchronously.
 */
export async function extractTextFromPdf(file: File): Promise<string> {
  try {
    const arrayBuffer = await file.arrayBuffer()
    const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer })
    const pdfDocument = await loadingTask.promise
    let extractedText = ''

    for (let pageNum = 1; pageNum <= pdfDocument.numPages; pageNum++) {
      const page = await pdfDocument.getPage(pageNum)
      const textContent = await page.getTextContent()
      const pageStrings = textContent.items
        .map((item: any) => (item && 'str' in item ? item.str : ''))
        .filter(Boolean)
      extractedText += pageStrings.join(' ') + '\n'
    }

    return extractedText.trim() || (await file.text())
  } catch (error) {
    console.warn('PDF.js parsing fallback to raw text:', error)
    try {
      return await file.text()
    } catch {
      return ''
    }
  }
}
