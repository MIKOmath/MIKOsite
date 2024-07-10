window.addEventListener('DOMContentLoaded', () => {
    var latexCodeTextarea = document.getElementById('latex_code');
    
    latexCodeTextarea.addEventListener('input', function(event) {
        var equationLabel = document.getElementById('preview');

        
        var latexCode = event.target.value;

        equationLabel.innerHTML =  latexCode
        try {
            renderMathInElement(document.getElementById('preview'), {
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
        }
        catch (error) {
        }
    });
});
    