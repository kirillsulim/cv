# {{data.personal.name}} {{data.personal.surname}}

{% if data.contacts.email %}
{{ gettext("email") }}: [{{data.contacts.email}}](mailto:{{data.contacts.email}})
{% endif %}

{% if data.contacts.site %}
{{ gettext("site") }}: [{{data.contacts.site}}]({{data.contacts.site}})
{% endif %}

{% if data.contacts.telegram %}
{{ gettext("telegram") }}: [{{data.contacts.telegram}}](https://t.me/{{data.contacts.telegram}})
{% endif %}

## {{ gettext("Work experience") }}

{% for job in data.work_experience|reverse %}

### {{job.position}} {{ gettext("at") }} {{job.organisation.name}}
{{job.from_date}} - {% if job.current %}{{ gettext("Present") }}{% else %}{{job.to_date}}{% endif %}
{% if job.summary %}{{job.summary}}{% endif %}
{% for bullet in job.bullets %}- {{bullet}}{% endfor %}

{% if job.technologies %}
{{ gettext("Key skills") }}: {{job.technologies | join(", ")}}
{% endif %}

{% endfor %}

## {{ gettext("Education") }}

{% for education in data.education|reverse %}
### {{education.university}} / {{education.faculty}}
{{education.degree}} {{education.speciality}}
{% endfor %}
