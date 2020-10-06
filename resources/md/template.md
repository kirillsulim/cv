# {{data.personal.name}} {{data.personal.surname}}

{% if data.contacts.email %}
email: [{{data.contacts.email}}](mailto:{{data.contacts.email}})
{% endif %}

{% if data.contacts.site %}
site: [{{data.contacts.site}}]({{data.contacts.site}})
{% endif %}

{% if data.contacts.phone %}
phone: {{data.contacts.phone}}
{% endif %}


## Work Experience

{% for job in data.work_experience|reverse %}

### {{job.position}} at {{job.organisation.name}}
{{job.from_date}} - {% if job.current %}Present{% else %}{{job.to_date}}{% endif %}
{% for bullet in job.bullets %}- {{bullet}}{% endfor %}

{% if job.technologies %}
Key skills: {{job.technologies | join(", ")}}
{% endif %}

{% endfor %}

## Education

{% for education in data.education|reverse %}
### {{education.university}} / {{education.faculty}}
{{education.speciality}}
{% endfor %}
