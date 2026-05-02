# Switch Interaction Sensor

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Integrazione custom per Home Assistant che monitora un'entità **switch** o **light** e crea un **binary sensor** che espone:

| Attributo          | Tipo  | Descrizione                                         |
|--------------------|-------|-----------------------------------------------------|
| `click_count`      | int   | Numero di toggle nella finestra temporale           |
| `interaction_type` | str   | `Physical` · `Automation` · `UI` · `Unknown`        |
| `user`             | str   | Nome utente HA (per UI) oppure `Unknown`            |
| `monitored_entity` | str   | L'entità monitorata                                 |
| `max_time_window`  | int   | Finestra configurata in secondi                     |

## Come funziona

Ogni volta che l'entità monitorata cambia stato (`on` ↔ `off`), l'integrazione analizza l'oggetto **context** dell'evento `state_changed`:

| Interazione | `context.parent_id` | `context.user_id` |
|-------------|---------------------|--------------------|
| Physical    | `None`              | `None`             |
| Automation  | valorizzato         | `None`             |
| UI          | `None`              | valorizzato        |

Riferimenti: [HA Context docs](https://data.home-assistant.io/docs/context/) · [Thread community](https://community.home-assistant.io/t/work-with-triggered-by-in-automations/400352/8)

Il binary sensor diventa **on** al primo click e resta attivo per `max_time` secondi dopo l'**ultimo** click, contando ogni toggle.  Alla scadenza della finestra il sensore va **off** e tutti i contatori si azzerano.

## Installazione (HACS)

1. Aprire HACS → **Integrazioni** → **⋮** → **Repository personalizzati**.
2. Aggiungere l'URL di questo repository, categoria **Integration**.
3. Installare **Switch Interaction Sensor**.
4. Riavviare Home Assistant.
5. Andare su **Impostazioni → Dispositivi e Servizi → Aggiungi Integrazione → Switch Interaction Sensor**.
6. Selezionare l'entità switch/light e la finestra temporale (default: 3 s).

## Installazione manuale

Copiare la cartella `custom_components/switch_interaction_sensor/` nella directory `<config>/custom_components/` e riavviare Home Assistant.

## Esempi di utilizzo

### Doppio click fisico → toggle luce soffitto

```yaml
automation:
  - alias: "Doppio click fisico accende luce soffitto"
    triggers:
      - trigger: state
        entity_id: binary_sensor.my_switch_interaction
        to: "off"
    conditions:
      - condition: template
        value_template: >
          {{ trigger.from_state.attributes.click_count == 2
             and trigger.from_state.attributes.interaction_type == 'Physical' }}
    actions:
      - action: light.toggle
        target:
          entity_id: light.ceiling
```

### Triplo click → attiva una scena

```yaml
automation:
  - alias: "Triplo click attiva modalità cinema"
    triggers:
      - trigger: state
        entity_id: binary_sensor.my_switch_interaction
        to: "off"
    conditions:
      - condition: template
        value_template: >
          {{ trigger.from_state.attributes.click_count == 3
             and trigger.from_state.attributes.interaction_type == 'Physical' }}
    actions:
      - action: scene.turn_on
        target:
          entity_id: scene.movie_mode
```

### Notifica quando un utente specifico agisce via UI

```yaml
automation:
  - alias: "Notifica admin su toggle del figlio"
    triggers:
      - trigger: state
        entity_id: binary_sensor.my_switch_interaction
        to: "off"
    conditions:
      - condition: template
        value_template: >
          {{ trigger.from_state.attributes.interaction_type == 'UI'
             and trigger.from_state.attributes.user == 'Figlio' }}
    actions:
      - action: notify.mobile_app_admin
        data:
          message: "Figlio ha premuto l'interruttore!"
```

## Lingue supportate

Inglese · Italiano · Francese · Spagnolo · Tedesco

## Licenza

MIT
