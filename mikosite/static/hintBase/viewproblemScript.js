window.addEventListener('DOMContentLoaded', () => {
    // Select all elements with the class 'clue'
    const clueElements = document.getElementsByClassName('clue');

    // Iterate over the collection of elements
    for (let i = 0; i < clueElements.length; i++) {
        try {
            // Render math in the current element
            renderMathInElement(clueElements[i], {
                delimiters: [
                    {left: "$$", right: "$$", display: true},
                    {left: "$", right: "$", display: false},
                    {left: "\\(", right: "\\)", display: false},
                    {left: "\\begin{equation}", right: "\\end{equation}", display: true},
                    {left: "\\begin{align}", right: "\\end{align}", display: true},
                    {left: "\\begin{alignat}", right: "\\end{alignat}", display: true},
                    {left: "\\begin{gather}", right: "\\end{gather}", display: true},
                    {left: "\\begin{CD}", right: "\\end{CD}", display: true},
                    {left: "\\[", right: "\\]", display: true}
                ],
                throwOnError: false
            });
        } catch (error) {
            console.error('Error rendering math in element:', clueElements[i], error);
        }
    }
    try {
            // Render math in the current element
            renderMathInElement(document.getElementById("latex-container"), {
                delimiters: [
                    {left: "$$", right: "$$", display: true},
                    {left: "$", right: "$", display: false},
                    {left: "\\(", right: "\\)", display: false},
                    {left: "\\begin{equation}", right: "\\end{equation}", display: true},
                    {left: "\\begin{align}", right: "\\end{align}", display: true},
                    {left: "\\begin{alignat}", right: "\\end{alignat}", display: true},
                    {left: "\\begin{gather}", right: "\\end{gather}", display: true},
                    {left: "\\begin{CD}", right: "\\end{CD}", display: true},
                    {left: "\\[", right: "\\]", display: true}
                ],
                throwOnError: false
            });
        } catch (error) {
            console.error('Error rendering math in element:', clueElements[i], error);
        }
});

document.addEventListener('click', function(event) {
    if (!event.target.classList.contains('clue')) {
      var spoilers = document.getElementsByClassName('clue');
      for (var i = 0; i < spoilers.length; i++) {
        spoilers[i].classList.remove('revealed');
      }
    }
  });
