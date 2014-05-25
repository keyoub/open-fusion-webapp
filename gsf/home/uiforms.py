from django import forms
from bootstrap3_datetime.widgets import DateTimePicker

# Choices variables for the forms select fields
LIVE_CHOICES = (
   ("cache", "Cached"),
   ("live", "Live"),
)

TWITTER_CHOICES = (
   ("image", "Images"),
   ("text", "Text"),
)

GSF_IMAGE_CHOICES = (
   ("imf", "With faces detected"),
   ("imb", "With bodies detected"),
)

OPERATORS = (
   ("", "equals"),
   ("__gt", "greater than"),
   ("__lt", "less than"),
   ("__gte", "greater than or equal"),
   ("__lte", "less than or equal"),
)

LOGICALS = (
   (0, "OR"),
   (1, "AND"), 
)

"""
   The form constructor for GSF data querying
"""
class GSFFusionForm(forms.Form):
   #live_option = forms.ChoiceField(required=False, choices=LIVE_CHOICES,
   #   widget=forms.RadioSelect(), initial="cache")

   images = forms.MultipleChoiceField(required=False,
      choices=GSF_IMAGE_CHOICES, widget=forms.CheckboxSelectMultiple())
      
   temperature_logic = forms.ChoiceField(label="Temperature (&deg;C)",
      required=False, choices=OPERATORS)
      
   temperature = forms.DecimalField(label="", required=False,
      help_text="eg. Temperature >= 22 &deg;C", min_value=-50, max_value=150
   )
                     
   humidity_logic  = forms.ChoiceField(label="Humidity",
      required=False, choices=OPERATORS)
      
   humidity = forms.DecimalField(label="", required=False,
      help_text="eg. humidity <= 60 %", min_value=1, max_value=100
   )
                  
   noise_level_logic  = forms.ChoiceField(label="Noise Level (dB)",
      required=False, choices=OPERATORS)
                     
   noise_level = forms.DecimalField(label="",required=False,
      help_text="eg. Noise level < 80 dB", min_value=-120, max_value=100
   )

"""
   The form constructor for Twitter querying
"""
class TwitterFusionForm(forms.Form):
   live_option = forms.ChoiceField(required=False, choices=LIVE_CHOICES,
      widget=forms.RadioSelect(), label="Data Type", initial="cache")
      
   options = forms.MultipleChoiceField(required=False, choices=TWITTER_CHOICES,
      widget=forms.CheckboxSelectMultiple())
      
   keywords = forms.CharField(required=False, help_text="eg. Wild OR Stallions")

"""
   The form constructor for twitter interface
"""
class TwitterForm(forms.Form):      
   addresses = forms.CharField(required=True, widget=forms.Textarea,
      label="*Addresses",
      help_text="""One address per line. Eg.<br /> Santa Cruz, CA
                   <br />Mission st, San Francisco""")
      
   radius = forms.FloatField(required=True, label="*Radius",
      help_text="in Kilometers", min_value = 0.1, max_value =5)

   options = forms.MultipleChoiceField(required=False, choices=TWITTER_CHOICES,
      widget=forms.CheckboxSelectMultiple())
      
   keywords = forms.CharField(required=False, 
      help_text="Space separated keywords")
      
   #addr = forms.CharField(required=True, max_length=500, label="*Address",
   #   help_text="eg. Santa Cruz, CA or Mission st, San Francisco")
      
   t_from = forms.DateTimeField(required=False, label="From",
      help_text="Enter starting date and time",
      widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm:ss"}))
      
   t_to = forms.DateTimeField(required=False, label="To",
      help_text="Enter ending date and time",
      widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm:ss"}))
   
"""
   The Aftershocks form constructor for GSF data querying
"""
class MiscForm(forms.Form):
   radius = forms.FloatField(required=False, label="Aftershock Radius (Km)",
      min_value = 0.1, max_value=5)
   
   addresses = forms.CharField(required=False, widget=forms.Textarea,
      help_text="""One address per line. Eg.<br /> Santa Cruz, CA
                   <br />Mission st, San Francisco""")
                   
   #live_option = forms.ChoiceField(required=False, choices=LIVE_CHOICES,
   #   widget=forms.RadioSelect())



