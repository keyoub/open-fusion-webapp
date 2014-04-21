$( document ).ready(function() {

   // Check the form for any cached data
   function check_form(form_name){
      var valid = false;
      $("#fuseform").find("input").each(function(){
         if ($(this).prop("id").indexOf(form_name) >= 0){
            if ($(this).prop("type") != "checkbox" &&
                $(this).val() != ""){
               valid = true;
            }
            if ($(this).prop("type") == "checkbox" &&
                $(this).prop("checked")){
               valid = true;
            }
         }
      });
      return valid;
   }
   
   // UI interaction between Epicenters and Aftershocks
   $("#aftEnable").click(function (){
      if (!check_form("epicenters")){
         alert("In order to get Aftershocks, you must have Epicenters.");
      }else{
         $(this).css("display", "none");
      }
   });

   // Custom form validation
   var frm = $("#fuseform");
   frm.submit(function(e){
      var input_flag = false;
      var valid_aftershocks = true;
      // Validate input form inputs
      $(this).find("input").each(function(){
         if ($(this).prop("type") == "hidden"){
            return;
         }
         if ($(this).prop("type") != "checkbox" && 
             $(this).val() != ""){
            if ($(this).prop("id").indexOf("aftershocks") >= 0){
               if ($("#id_gsf_aftershocks-radius").val() == ""){
                  valid_aftershocks = false;
               }
            }
            input_flag = true;
         }
         if ($(this).prop("type") == "checkbox" && 
             $(this).prop("checked")){
            if ($(this).prop("id").indexOf("aftershocks") >= 0){
               if ($("#id_gsf_aftershocks-radius").val() == ""){
                  valid_aftershocks = false;
               }
            }
            input_flag = true;
         }
      });
      if (!valid_aftershocks){
         e.preventDefault();
         alert("To get aftershocks you must enter a Radius.");
      }else if (!input_flag){
         e.preventDefault();
         alert("You can't expect results from nothing.");
      }else{
         NProgress.start();
      }
   });
   
   $( window ).unload(function() {
      NProgress.remove();
   });

   $("#epiModalLink").click(function(){
      $('#epiModal').modal();
   });

   $("#aftModalLink").click(function(){
      $('#aftModal').modal();
   });

   /****   The jQuery Toggle functions ****/
   var options = {
      effect: "slide", 
      duration: 400,
      easing: "easeOutCubic",
      direction: "up"
   }
   $("#twitterEpi").click(function () {
      $("#twtEpiDiv").toggle(options);
   });
   $("#twitterAft").click(function () {
      $("#twtAftDiv").toggle(options);
   });
   $("#gsfEpi").click(function () {
      $("#gsfEpiDiv").toggle(options);
   });
   $("#gsfAft").click(function () {
      $("#gsfAftDiv").toggle(options);
   });

   // Check the forms on load and open them if they have cached data
   if (check_form("twitter_epicenters")){
      $("#aftEnable").trigger("click");
      $("#twtEpiDiv").toggle(options);
   }
   if (check_form("gsf_epicenters")){
      $("#aftEnable").trigger("click");
      $("#gsfEpiDiv").toggle(options);
   }
   if (check_form("twitter_aftershocks")){
      $("#twtAftDiv").toggle(options);
   }
   if (check_form("gsf_aftershocks")){
      $("#gsfAftDiv").toggle(options);
   }
});
