# Long report rendering on mobile

The user reported repeated page failures when switching into long sample reports in Safari on mobile, while desktop browsers worked. The exact device and OS version were unavailable, so the original iOS process failure has not been reproduced or diagnosed conclusively.

Code inspection found that every report block and inline SVG was mounted at once and sanitized again on parent renders. The public report container also retained a transform animation. Private completed reports fetched and reconstructed the entire view every three seconds. Public tab navigation uses history pushState, not an HTTP redirect.

Small or touch screens now paginate reports exceeding 40,000 markup characters or 20 blocks. A page contains up to six blocks with a 16,000-character grouping target; section boundaries remain visible. Oversized HTML is divided at top-level elements, and ordinary tables split between rows while retaining their headers. Row-spanning tables, individual oversized elements and SVGs remain intact to preserve their semantics, so the target is not a hard memory bound for any possible single element. Only the selected page is mounted. A table of contents and previous/next controls expose every page; the complete HTML download remains the route for printing the full document.

Displayed HTML remains sanitized, and unchanged HTML/SVG strings reuse the sanitized result within their mounted component. Large report containers no longer carry transform animations. Private view polling runs serially while a project is running or queued, stops when it pauses or finishes, and restarts after an action resumes the run. Stale public and polling requests are aborted on cleanup.

Validation: the build and production gateway test passed. Eight targeted report/navigation tests passed in both Edge and Playwright WebKit 26.6 on Windows. The stress report contained 16 diagrams with 300 circles each, 128 marked paragraphs and 120 marked table rows plus a final paragraph. Every figure and all 249 content markers remained reachable, mounted report content stayed below 900 elements in that fixture, and 12 report/solution tab switches caused no document reload or page error. The real frozen report fixture retained all 24 diagrams across mobile pages and the complete desktop view. Polling stopped after completion and resumed after a new analysis action. These results are browser-engine regression checks, not a claim of testing on the user's iPhone.

Deployment is tracked separately; this document alone does not claim that the change is live.
