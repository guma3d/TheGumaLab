document.getElementById('search-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const query = document.getElementById('search-query').value.trim();
    if (!query) return;

    const btnText = document.querySelector('.btn-text');
    const loader = document.querySelector('.loader');
    const btn = document.getElementById('submit-btn');
    const resultContainer = document.getElementById('result-container');

    // Simulate search loading state
    btn.disabled = true;
    btnText.style.display = 'none';
    loader.style.display = 'block';
    
    setTimeout(() => {
        // Reset button
        btn.disabled = false;
        btnText.style.display = 'block';
        loader.style.display = 'none';
        
        // Show simulated result
        resultContainer.classList.remove('hidden');
        document.querySelector('.result-msg').innerHTML = `Search simulated for: "<b>${query}</b>"<br>Images will be displayed here eventually!`;
    }, 1500);
});
