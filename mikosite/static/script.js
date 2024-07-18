document.addEventListener('DOMContentLoaded', function() {
  const navbarToggle = document.querySelector('.navbar-toggle');
  const navbarCenter = document.querySelector('.navbar-center');

  navbarToggle.addEventListener('click', function() {
    navbarCenter.classList.toggle('active');
  });
});