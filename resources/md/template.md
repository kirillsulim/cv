# {{data.personal.name}} {{data.personal.surname}}

{% if data.contacts.email %}
{% trans %}email: {% endtrans %}[{{data.contacts.email}}](mailto:{{data.contacts.email}})
{% endif %}

{% if data.contacts.site %}
{% trans %}site: {% endtrans %}[{{data.contacts.site}}]({{data.contacts.site}})
{% endif %}

{% if data.contacts.telegram %}
{% trans %}telegram: {% endtrans %}[{{data.contacts.telegram}}](https://t.me/{{data.contacts.telegram}})
{% endif %}

{% if data.contacts.phone %}
{% trans %}phone: {% endtrans %}{{data.contacts.phone}}
{% endif %}


## {% trans %}Work experience{% endtrans %}

{% for job in data.work_experience|reverse %}

### {{job.position}} {% trans %}at{% endtrans %} {{job.organisation.name}}
{{job.from_date}} - {% if job.current %}{% trans %}Present{% endtrans %}{% else %}{{job.to_date}}{% endif %}
{% for bullet in job.bullets %}- {{bullet}}{% endfor %}

{% if job.technologies %}
{% trans %}Key skills: {% endtrans %}{{job.technologies | join(", ")}}
{% endif %}

{% endfor %}

## {% trans %}Education{% endtrans %}

{% for education in data.education|reverse %}
### {{education.university}} / {{education.faculty}}
{{education.speciality}}
{% endfor %}
