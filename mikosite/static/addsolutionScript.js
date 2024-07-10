document.getElementById('add-hint-button').addEventListener('click', function() {
    // Determine the index for the new hint field
    var index = document.querySelectorAll('[id^="hint"]').length + 1;
    
    // Create a new hint field and label
    var div = document.createElement('div');
    div.classList.add('form-field');
    div.innerHTML = '<label for="hint' + index + '">Hint ' + index + ':</label>' +
                    '<input type="text" id="hint' + index + '" name="hint' + index + '">' +
                    '<label id="compiled'+ index + '" style="font-weight: normal">' + '</label>';
    
    // Append the new hint field to the form
    document.getElementById('additional-hints').appendChild(div);

    var hintNumber = index;
    var compiledElement = document.getElementById('compiled' + hintNumber);
    hint = document.getElementById('hint' + hintNumber);

    hint.addEventListener('input', function(event) {
        var latexCode = event.target.value;
        compiledElement.innerHTML = latexCode;

        try {
            renderMathInElement(compiledElement, {
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
            console.log(error);
        }
    });

});


window.addEventListener('DOMContentLoaded', () => {
    var allHints = document.querySelectorAll('[id^="hint"]');
    
    allHints.forEach(function(hint) {
        var hintNumber = hint.id.replace('hint', '');
        var compiledElement = document.getElementById('compiled' + hintNumber);
        
        hint.addEventListener('input', function(event) {
            var latexCode = event.target.value;
            compiledElement.innerHTML = latexCode;

            try {
                renderMathInElement(compiledElement, {
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
                console.log(error);
            }
        });
    });

    solution_area = document.getElementById("solution");
    solution_compiled = document.getElementById("solutioncompiled");

    solution_area.addEventListener('input', function(event) {
        var latexCode = event.target.value;
        solution_compiled.innerHTML = latexCode;

        try {
            renderMathInElement(solution_compiled, {
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
            console.log(error);
        }
    });
    try {
        renderMathInElement(document.getElementById("preview"), {
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
        console.log(error);
    }

});