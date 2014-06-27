$( document ).ready(function() {

   // Check the form for any cached data
   function check_form(form_name){
      var valid = false;
      $("#fuseform").find("input, textarea").each(function(){
         if ($(this).prop("id").indexOf(form_name) >= 0 &&
             $(this).prop("id").indexOf("live_option") < 0){
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
      if (!check_form("epicenters") &&
          !check_form("addresses")){
         alert("In order to get Aftershocks, you must have Epicenters.");
      }else{
         $(this).css("display", "none");
      }
   });

   // Custom form validation on submit
   var frm = $("#fuseform");
   frm.submit(function(e){
      if (check_form("aftershocks") || check_form("radius")){
         if($("#id_misc_form-radius").val() == ""){
            e.preventDefault();
            alert("To get aftershocks you must enter a Radius.");
            return;
         }else if (!check_form("epicenters") &&
                   !check_form("addresses")){
            e.preventDefault();
            alert("In order to get Aftershocks, you must have Epicenters.");
            return; 
         }
      }
      else if (!check_form("id")){
         e.preventDefault();
         alert("You can't expect results from nothing.");
         return;
      }
      NProgress.start();
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
   $("#addrToggle").click(function () {
      $("#addrDiv").toggle(options);
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
   if (check_form("addresses")){
      $("#aftEnable").trigger("click");
      $("#addrDiv").toggle(options);
   }
   if (check_form("twitter_aftershocks")){
      $("#twtAftDiv").toggle(options);
   }
   if (check_form("gsf_aftershocks")){
      $("#gsfAftDiv").toggle(options);
   }
   
   function resetForm($form) {
      $("#fuseform").find("input, textarea").each(function(){
         if ($(this).prop("id").indexOf("live_option") < 0 &&
             $(this).prop("type").indexOf("hidden") < 0){
            $(this).val("");
         }
      });
      $("#fuseform").find("input:checkbox").each(function(){
         if ($(this).prop("id").indexOf("live_option") < 0){
            $(this).removeAttr('checked');
         }
      });
   }
   
   // Cache and live search switches
   /*
   $("#id_misc_form-live_option_0").click(function () {
      //resetForm($("#fuseform"));
      //$("#aftEnable").css("display", "none");
      $("#twitterEpi").css("display", "none");
      $("#twtEpiDiv").css("display", "none");
      $("#gsfEpi").css("display", "none");
      $("#gsfEpiDiv").css("display", "none");
      $("#gsfAft").css("display", "none");
      $("#gsfAftDiv").css("display", "none");      
   });
   
   $("#id_misc_form-live_option_1").click(function () {
      //resetForm($("#fuseform"));
      $("#twitterEpi").css("display", "");
      $("#twtEpiDiv").css("display", "");
      $("#gsfEpi").css("display", "");
      $("#gsfEpiDiv").css("display", "");
      $("#gsfAft").css("display", "");
      $("#gsfAftDiv").css("display", "");      
   });
   
   if ($("#id_misc_form-live_option_0").is(":checked")){
      $("#twitterEpi").css("display", "none");
      $("#twtEpiDiv").css("display", "none");
      $("#gsfEpi").css("display", "none");
      $("#gsfEpiDiv").css("display", "none");
      $("#gsfAft").css("display", "none");
      $("#gsfAftDiv").css("display", "none");
      //$("#id_misc_form-live_option_0").trigger("click");
   }
   */
   
   // Initialize the UI sliders
   /*$("#id_gsf_epicenters-temperature").slider({});
   $("#id_gsf_epicenters-humidity").slider({});
   $("#id_gsf_epicenters-noise_level").slider({});
   
   $("#id_gsf_aftershocks-temperature").slider({});
   $("#id_gsf_aftershocks-humidity").slider({});
   $("#id_gsf_aftershocks-noise_level").slider({});*/
   
});
