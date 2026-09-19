# Invariants

The rules that must still hold after any change. Each one links to the document that argues it.

## The seven

1. **Idempotent.** `process(process(text)) == process(text)`, for every document, always. The
   pre-commit hook is unusable without it: a hook that changes a file on every run never lets a
   commit through.
   [02-scanning-and-splicing.md#idempotency](02-scanning-and-splicing.md#idempotency)

2. **Annotation-preserving.** The annotation line comes out byte-for-byte as the author wrote it.
   It is an input to the tool, never an output.
   [01-annotation-syntax.md#grammar](01-annotation-syntax.md#grammar)

3. **Fence-aware.** An annotation inside a fenced code block is content, not an annotation. This
   is what lets the project document its own syntax.
   [02-scanning-and-splicing.md#fence-awareness](02-scanning-and-splicing.md#fence-awareness)

4. **The body is the only thing written.** Within a region, the tool rewrites the block body; the
   fence line is touched only to lengthen a fence that the body would otherwise close.
   [02-scanning-and-splicing.md#the-region](02-scanning-and-splicing.md#the-region)

5. **No trailing whitespace, LF endings, one final newline.** Output that another pre-commit hook
   would want to change is output that makes the run non-terminating.
   [02-scanning-and-splicing.md#whitespace](02-scanning-and-splicing.md#whitespace)

6. **Failure is loud and located.** Every error names the Markdown file and the annotation's line
   number, and no failure ever results in a written file: a document is spliced only once all of
   its regions have been extracted.
   [03-extraction.md#errors-carry-a-location](03-extraction.md#errors-carry-a-location)

7. **Nothing is imported, nothing is executed.** Extraction is static parsing. A hook that runs on
   every commit must not run the code it reads.
   [03-extraction.md#python-symbols](03-extraction.md#python-symbols)

## Canonical decision-makers

One question, one function. When a second call site needs the same answer, it calls the same
function rather than reimplementing the decision next to itself.

| Question | Owner |
| -------- | ----- |
| Is this line an annotation, and what does it say? | `_annotation.parse` |
| Where does this region start and end? | `_document.scan` |
| Is this line a fence, and does it close that one? | `_document` (fence helpers) |
| What filesystem path does this target name? | `_resolve.resolve` |
| Where is the project root? | `_resolve.find_root` |
| What does this selector extract? | `_extract.extract` |
| Which lines define this symbol? | `_extract._python` (span helpers) |
| How long must this fence be? | `_render.fence_length` |
| What does the body look like? | `_render.render_body` |
| What language does this extension imply? | `_lang.language_for` |

## Fragile couplings

- **Dedent and re-indent are two halves of one rule.** Extraction normalizes content to column
  zero; rendering applies the document's indentation. Either one alone produces a block at the
  wrong column, and the failure is invisible in a diff of a single file.
- **Fence escalation and body content.** The fence length depends on the body, so it must be
  computed after extraction and before the fence line is written. Computing it from the author's
  original fence is the bug waiting to happen.
- **`--check` and rewrite must share one code path.** They differ only in whether the result is
  written. Any divergence means `--check` passes on a file the rewrite would change, which is the
  one failure a CI gate cannot tolerate.
