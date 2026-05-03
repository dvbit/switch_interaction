# Switch Interaction Sensor

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Integrazione custom per Home Assistant che monitora un'entità **switch** o **light** e crea un **device** con quattro entità:

| Entità              | Tipo          | Descrizione                                       |
|---------------------|---------------|---------------------------------------------------|
| Window              | binary_sensor | `on` mentre la finestra click è attiva            |
| Click Count         | sensor        | Numero di toggle nell'ultima finestra             |
| Interaction Type    | sensor        | `Physical` · `Automation` · `UI` · `Unknown`      |
| User                | sensor        | Nome utente HA (per UI) oppure `Unknown`          |

Tutti i valori dei sensori sono **persistenti** — mostrano sempre l'ultima interazione e si aggiornano solo al prossimo toggle.

## Come funziona

Ogni volta che l'entità monitorata cambia stato (`on` ↔ `off`), l'integrazione analizza l'oggetto **context**:

| Interazione | `context.parent_id` | `context.user_id` |
|-------------|---------------------|--------------------|
| Physical    | `None`              | `None`             |
| Automation  | valorizzato         | `None`             |
| UI          | `None`              | valorizzato        |

## Installazione (HACS)

1. HACS → **Integrazioni** → **⋮** → **Repository personalizzati** → aggiungere URL repo, categoria **Integration**.
2. Installare **Switch Interaction Sensor** e riavviare HA.
3. **Impostazioni → Dispositivi e Servizi → Aggiungi Integrazione → Switch Interaction Sensor**.
4. Selezionare entità, finestra temporale e nome dispositivo (default: `int_<nome_entità>`).

## Esempi di utilizzo

### Doppio click fisico → toggle luce soffitto

```yaml
automation:
  - alias: "Doppio click fisico accende soffitto"
    triggers:
      - trigger: state
        entity_id: binary_sensor.int_luce_cucina_window
        to: "off"
    conditions:
      - condition: state
        entity_id: sensor.int_luce_cucina_click_count
        state: "2"
      - condition: state
        entity_id: sensor.int_luce_cucina_interaction_type
        state: "Physical"
    actions:
      - action: light.toggle
        target:
          entity_id: light.ceiling
```

### Notifica quando un utente specifico agisce via UI

```yaml
automation:
  - alias: "Notifica su toggle del figlio"
    triggers:
      - trigger: state
        entity_id: sensor.int_luce_cucina_interaction_type
    conditions:
      - condition: state
        entity_id: sensor.int_luce_cucina_user
        state: "Figlio"
    actions:
      - action: notify.mobile_app_admin
        data:
          message: "Figlio ha premuto l'interruttore!"
```

## Lingue supportate

Inglese · Italiano · Francese · Spagnolo · Tedesco

## Licenza

MIT
