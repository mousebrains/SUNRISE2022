function toggleSidebar() {
  sidebar = document.getElementById("sidebar");
  sidebarToggle = document.getElementById("sidebar-toggle-button");

  if (sidebar.style.display == "none") {
    sidebar.style.display = "flex";
    sidebarToggle.innerHTML = '&rsaquo;';
  } else {
    sidebar.style.display = "none";
    sidebarToggle.innerHTML = '&lsaquo;';
  }

}

function toggleVerticalCollapsable(toggleButton, elementId, display) {
  element = document.getElementById(elementId);
  arrow = toggleButton.getElementsByClassName('vertical-toggle-arrow')[0];
  if (element.style.display == "none") {
    element.style.display = display;
    arrow.innerHTML = '&#65087';
  } else {
    element.style.display = "none";
    arrow.innerHTML = '&#65088'
  }
}
