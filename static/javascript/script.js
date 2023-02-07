// DARK MODE 1



// var theme = window.localStorage.currentTheme;

// $("body").addClass(theme);

// if ($("body").hasClass("night")) {
//   $(".dntoggle").addClass("fas fa-sun");
//   $(".dntoggle").removeClass("fas fa-moon");
// } else {
//   $(".dntoggle").removeClass("fas fa-sun");
//   $(".dntoggle").addClass("fas fa-moon");
// }

// $(".dntoggle").click(function () {
//   $(".dntoggle").toggleClass("fas fa-sun");
//   $(".dntoggle").toggleClass("fas fa-moon");

//   if ($("body").hasClass("night")) {
//     $("body").toggleClass("night");
//     localStorage.removeItem("currentTheme");
//     localStorage.currentTheme = "day";
//   } else {
//     $("body").toggleClass("night");
//     localStorage.removeItem("currentTheme");
//     localStorage.currentTheme = "night";
//   }
// });


// function darkmode(){
//     var SetTheme = document.body;
//     SetTheme.classList.toggle("night")
//     var theme;
//     if(SetTheme.classList.contains("night")){
//         console.log("Dark mode");
//         theme = "DARK";
//     }else{
//         console.log("Light mode");
//         theme = "LIGHT";
//     }
//     // save to localStorage
//     localStorage.setItem("PageTheme", JSON.stringify(theme));
//     // ensure you convert to JSON like i have done -----JSON.stringify(theme)
// }

// setInterval(() => {
//     let GetTheme = JSON.parse(localStorage.getItem("PageTheme"));
//     console.log(GetTheme);
//     if(GetTheme === "DARK"){
//         document.body.classList = "night";
//     }else{
//         document.body.classList = "";
//     }
// }, 5);





// DARK MODE 2

// // check for saved 'darkMode' in localStorage
// let darkMode = localStorage.getItem('darkMode'); 

// const darkModeToggle = document.querySelector('#dark-mode-toggle');

// const enableDarkMode = () => {
//   // 1. Add the class to the body
//   document.body.classList.add('night');
//   // 2. Update darkMode in localStorage
//   localStorage.setItem('darkMode', 'enabled');
// }

// const disableDarkMode = () => {
//   // 1. Remove the class from the body
//   document.body.classList.remove('night');
//   // 2. Update darkMode in localStorage 
//   localStorage.setItem('darkMode', null);
// }
 
// // If the user already visited and enabled darkMode
// // start things off with it on
// if (darkMode === 'enabled') {
//   enableDarkMode();
// }

// // When someone clicks the button
// darkModeToggle.addEventListener('click', () => {
//   // get their darkMode setting
//   darkMode = localStorage.getItem('darkMode'); 
  
//   // if it not current enabled, enable it
//   if (darkMode !== 'enabled') {
//     enableDarkMode();
//   // if it has been enabled, turn it off  
//   } else {  
//     disableDarkMode(); 
//   }
// });





// DARK MODE 3


const darkBtn = document.querySelector('.dntoggle');
const fronthead = document.querySelector('.hero');
const bodyEl = document.querySelector('body');
const navbar = document.querySelector('#navbar')
const navlink = document.querySelectorAll('#navlinks')
const usericon = document.querySelector('#usericon')
const closeBtn = document.querySelector('.btn-close')
// const darkMode = () => {
//     bodyEl.classList.toggle('night');
//     navbar.classList.toggle('night');
//     for(nav of navlink){
//         nav.classList.toggle('light')
//     }

// }

// darkBtn.addEventListener('click', () => {
//     // Get the value of the "dark" item from the local storage on every click
//     setDarkMode = localStorage.getItem('dark');

//     if(setDarkMode !== "on") {
//         darkMode();
//         // Set the value of the itwm to "on" when dark mode is on
//         setDarkMode = localStorage.setItem('dark', 'on');
//         darkBtn.classList.remove('fa-moon')
//         darkBtn.classList.add('fa-sun')
//     } else {
//         darkMode();
//         // Set the value of the item to  "null" when dark mode if off
//         setDarkMode = localStorage.setItem('dark', null);
//         darkBtn.classList.remove('fa-sun')
//         darkBtn.classList.add('fa-moon')
//     }
// });

// // Get the value of the "dark" item from the local storage
// let setDarkMode = localStorage.getItem('dark');

// // Check dark mode is on or off on page reload
// if(setDarkMode === 'on') {
//     darkMode();
// }

//********************** */

// image upload click


function chooseFile() {
    document.getElementById("fileInput").click();
  }

  //************************* */

  let timer = 1
  const timeout = ()=>{
  let myTimer =  setInterval(()=>{
        if(timer===0){
            closeBtn.click()
            clearInterval(myTimer)
        }
        else{
            timer--
        }
        console.log(timer)
    },1000) 
  }
  window.addEventListener('DOMContentLoaded',timeout
  )



// ANOTHER CODE


//****************************************************** */

// document.querySelector('.dntoggle').addEventListener('click', function() {
//     var wasDarkMode = localStorage.getItem('darkmode') === '1';
//     // darkBtn.classList.toggle('fa-sun')

//     localStorage.setItem('darkmode', wasDarkMode ? '0' : '1');
//     h = document.documentElement.classList[wasDarkMode ? 'remove' : 'add']('darkmode');
//   });

// if (h[wasDarkMode ? 'add': 'remove']('darkmode')) {
//     darkBtn.classList.add('fa-sun');
// }




// ANOTHER CODE


// document.addEventListener("DOMContentLoaded", function() {
//     var wasDarkMode = localStorage.getItem('darkmode') === '1';
//     var toggleIcon = document.querySelector('.dntoggle');
  
//     if (wasDarkMode) {
//         navbar.classList.add('night')
//         fronthead.classList.add('herroo')
//         bodyEl.classList.remove('night');
//       toggleIcon.classList.remove('fa-moon');
//       toggleIcon.classList.add('fa-sun');
//     } else {
//         // bodyEl.classList.add('light');
//       toggleIcon.classList.remove('fa-sun');
//       toggleIcon.classList.add('fa-moon');
//     }
  
//     document.querySelector('.dntoggle').addEventListener('click', function() {
//       wasDarkMode = localStorage.getItem('darkmode') === '1';
//       localStorage.setItem('darkmode', wasDarkMode ? '0' : '1');
//       if (wasDarkMode) {
        // bodyEl.remove('night'); // I DONT KNOW WHY THIS MAKES THE PAGE BLANK WHEN SWITCHED TO LIGHT MODE 
        // bodyEl.classList.add('light');
//         toggleIcon.classList.remove('fa-sun');
//         toggleIcon.classList.add('fa-moon');
//       } else {
//         bodyEl.classList.remove('light');
//         bodyEl.classList.toggle('night');
//         toggleIcon.classList.remove('fa-moon');
//         toggleIcon.classList.add('fa-sun');
//       }
//     });
//   });
  
  


// ANOTHER CODE
  
// document.addEventListener("DOMContentLoaded", function() {
//     var wasDarkMode = localStorage.getItem('darkmode') === '1';
//     var toggleIcon = document.querySelector('.dntoggle');
  
//     navbar.classList.add(wasDarkMode ? 'night' : 'light');
//     toggleIcon.classList.remove(wasDarkMode ? 'fa-moon' : 'fa-sun');
//     toggleIcon.classList.add(wasDarkMode ? 'fa-sun' : 'fa-moon');
  
//     document.querySelector('.dntoggle').addEventListener('click', function() {
//       wasDarkMode = localStorage.getItem('darkmode') === '1';
//       localStorage.setItem('darkmode', wasDarkMode ? '0' : '1');
//       navbar.classList.remove(wasDarkMode ? 'night' : 'light');
//       navbar.classList.add(wasDarkMode ? 'light' : 'night');
//       bodyEl.classList.remove(wasDarkMode ? 'night' : 'light');
//       bodyEl.classList.add(wasDarkMode ? 'light' : 'night');
//     //   fronthead.classList.add(wasDarkMode ? 'light' : 'night')
//       toggleIcon.classList.remove(wasDarkMode ? 'fa-moon' : 'fa-sun');
//       toggleIcon.classList.add(wasDarkMode ? 'fa-sun' : 'fa-moon');
//     });
// });



//  OPTIMIZED


// document.addEventListener("DOMContentLoaded", function() {
//     var darkmode = localStorage.getItem('darkmode') === '1';
//     var toggleIcon = document.querySelector('.dntoggle');
  
//     navbar.classList.add(darkmode ? 'night' : 'light');
//     toggleIcon.classList.replace(darkmode ? 'fa-moon' : 'fa-sun', darkmode ? 'fa-sun' : 'fa-moon');
  
//     document.querySelector('.dntoggle').addEventListener('click', function() {
//       darkmode = !darkmode;
//       localStorage.setItem('darkmode', darkmode ? '1' : '0');
//       navbar.classList.replace(darkmode ? 'light' : 'night', darkmode ? 'night' : 'light');
//       toggleIcon.classList.replace(darkmode ? 'fa-sun' : 'fa-moon', darkmode ? 'fa-moon' : 'fa-sun');
//     });
// });



// EXPLANATION

// 1. First, the DOMContentLoaded event listener is attached to the document. This ensures that the code inside the listener function will only be executed once the entire HTML document has been loaded and parsed.
// 2. The var darkmode variable is used to store the state of the theme (dark mode or light mode). The value is obtained from local storage by using localStorage.getItem('darkmode'), which retrieves the value of the 'darkmode' item in local storage. If the value is '1', it means the theme was previously set to dark mode, so darkmode is set to true. If the value is not '1', it means the theme was not previously set to dark mode, so darkmode is set to false.
// 3. The var toggleIcon variable is used to store a reference to the element with class dntoggle. This element is the toggle button that will be used to switch between dark mode and light mode.
// 4. The navbar element's class list is updated using .add() method and the ternary operator. If darkmode is true, the 'night' class is added. If darkmode is false, the 'light' class is added.
// 5. The toggleIcon element's class list is updated using .replace() method and the ternary operator. If darkmode is true, the 'fa-sun' class is replaced with 'fa-moon'. If darkmode is false, the 'fa-moon' class is replaced with 'fa-sun'.
// 6. An event listener is attached to the toggle button using .addEventListener('click', function() { ... }). This listener function will be executed every time the toggle button is clicked.
// 7. Inside the event listener function, darkmode is negated using !darkmode. This means that if darkmode was true, it will now be false, and vice versa.
// 8. The new state of the theme (dark mode or light mode) is saved to local storage using localStorage.setItem('darkmode', darkmode ? '1' : '0'). If darkmode is true, the value '1' is saved. If darkmode is false, the value '0' is saved.
// 9. The navbar element's class list is updated again using .replace() method and the ternary operator. If darkmode is true, the 'light' class is replaced with 'night'. If darkmode is false, the 'night' class is replaced with 'light'.
// 10. The toggleIcon element's class list is updated one final time using .replace() method and the ternary operator. If darkmode is true, the 'fa-sun' class is replaced with 'fa-moon'. If darkmode is false, the 'fa-moon' class is replaced with 'fa-sun'.


// THIS IS THE JQUERY CODE BELOW

$(document).ready(function() {
    var wasDarkMode = localStorage.getItem('darkmode') === '1';
    var $toggleIcon = $('.dntoggle');
  
    if (wasDarkMode) {
        $('navbar').addClass('night');
        $toggleIcon.removeClass('fa-sun').addClass('fa-moon');
    } else {
        $toggleIcon.removeClass('fa-moon').addClass('fa-sun');
    }
  
    $('.dntoggle').click(function() {
        wasDarkMode = localStorage.getItem('darkmode') === '1';
        localStorage.setItem('darkmode', wasDarkMode ? '0' : '1');
      
        if (wasDarkMode) {
            $('body').removeClass('night');
            $toggleIcon.removeClass('fa-moon').addClass('fa-sun');
        } else {
            $('body').addClass('night');
            $toggleIcon.removeClass('fa-sun').addClass('fa-moon');
        }
    });
});
