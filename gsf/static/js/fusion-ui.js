$( document ).ready(function() {
   
   function check_epicenters(form_id){
      var id = new Array();
      var valid_epi = false;
      $("#fuseform").find("input").each(function(){
         if ($(this).prop("id").indexOf("epicenters") >= 0){
            if ($(this).prop("type") != "checkbox" &&
                $(this).val() != ""){
               valid_epi = true;
               id.push("kir");
            }
            if ($(this).prop("type") == "checkbox" &&
                $(this).prop("checked")){
               valid_epi = true;
               id.push("chor");
            }
         }
      });
      return (form_id ? id : valid_epi);
   }
   
   var id = check_epicenters(true);
   if (id.length > 0){
      alert(id);
   }

   // UI interaction between Epicenters and Aftershocks
   $("#aftEnable").click(function (){
      var valid_epi = check_epicenters(false);
      if (!valid_epi){
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

});
