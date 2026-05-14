---
type: concept
tags: [ui, ux, state, lifecycle, ab-testing, dashboards, product-thinking]
created: 2026-05-13
updated: 2026-05-13
recency: 2026-05-13
confidence: high
related: ["[[wiki/concepts/ab-experiment-product-thinking]]", "[[wiki/concepts/component-reuse-discipline]]"]
source: Geo direct dictation 2026-05-13 после катастрофы 'запустил тест, статистики не вижу, юки стоит хотя я отключил'
---

# Stateful UI lifecycle — что показывать в каком состоянии

## TL;DR

Если экран связан с **процессом который имеет состояние** (запущен / идёт / приостановлен / завершён / применён) — UI должен **визуально кардинально отличаться** в каждом состоянии. Не «бейдж 'running'», а **другая структура секции**, другие данные, другие action-кнопки.

Корневая ошибка: разработчик делает один layout «настройка теста», ставит сверху бейдж «running» — и не показывает ничего из того что реально идёт. User запустил тест и не понимает что происходит.

## Real catastrophe (13.05.2026)

Цитата пользователя:
> «Я сейчас запустил новый тест, я не вижу никакой информации о том, что он запущен. Да, мне там выпустилось, тест запущен. А где, блядь, теперь статистика? Во-первых, я вижу в ротации сейчас информацию о том, что у меня юки стоит. Хотя юки быть не должно. Я выбрал, что юки мы отключаем.»
>
> «Дальше я хочу видеть, как идет это тестирование. Я хочу видеть по нему статистику, что вот сейчас мы тестируем вместо юки вот такой оффер, потом вот такой. Поэтому набрано столько-то кликов EPC такой-то.»
>
> «Ты как UI UX не продумал этого. Ты разработал это и не протестировал, как оно будет выполняться. Ты нарушил все протоколы.»

Что было сделано: запустил тест → в ротации остался **старый базовый** + бейдж «тест идёт» где-то наверху. **Никакой связи** между «тест идёт» и тем что показывается в ротации.

Что должно было: после запуска теста ротация в UI **меняется**:
- Вместо отключённого оффера показывается **placeholder** «🔄 Тестовая позиция»
- Под раскрытием — какие офферы катятся, их кликов, EPC
- Каждая ротация = новая запись «вот такой оффер шёл, набрал X кликов»

## Принцип

Для каждого экрана с процессом **перечислить все состояния**, и для каждого:

1. **Что визуально меняется** (структура секции, не только бейдж)
2. **Какие данные показываются** (новые поля релевантные именно этому state)
3. **Какие actions доступны** (новые кнопки / отключённые старые)

### Пример для A/B эксперимента

| State | Структура UI | Данные | Actions |
|---|---|---|---|
| `idle` (нет теста) | Toolbar с настройкой + Run button | Прошлые завершённые тесты в истории | "Запустить новый тест" |
| `running` | Live-секция «Накапливаем данные» наверху + старая ротация ниже **с placeholder'ами** на тестовых позициях | Кликов, EPC, время с момента запуска, текущий вариант в эфире, raw bandit log | "Стоп / пауза / форсировать промот" |
| `paused` | Live-секция grayed-out + кнопка resume | Снимок данных на момент паузы | "Resume / завершить" |
| `completed` | Результат — победитель + lift% + рекомендация | Финальная статистика, история ротаций, время | "Применить как новый base / отбросить / запустить новый" |
| `promoted` | Confirmation — variant X теперь базовый, с какого момента | История промотов с диапазонами дат | "Откатить / запустить новый над новым базовым" |

## Чек-лист для каждого stateful экрана

Перед тем как делать screen-spec, ответить:

1. **Какие состояния может иметь объект на экране?**
   - Перечислить **все**, не только happy path
2. **Что user должен видеть в каждом состоянии?**
   - Не «бейдж», а **другая структура** секций
3. **Какие данные релевантны для каждого state?**
   - В running — live кликов/EPC. В idle — этого нет.
   - В completed — финальный результат. В running — промежуточный.
4. **Какие actions доступны в каждом state?**
   - В running нельзя «запустить ещё один тот же», но можно «стоп».
   - В completed нельзя «продолжить», но можно «применить».
5. **Что показывается ВМЕСТО «удалённых» элементов?**
   - User отключил оффер X из ротации. В running на месте X должно быть «🔄 Тестовая позиция: текущий вариант Y». Не пустота, не «X disabled». А **что реально сейчас в эфире**.
6. **Как user мгновенно понимает что экран в state Z?**
   - Не «маленький бейдж в углу», а **главное содержание секции меняется**.

## Anti-patterns

- ❌ **Бейдж «running» без изменения остальной структуры.** User видит ту же ротацию которая была до запуска. Думает «ничего не происходит».
- ❌ **«Disabled» элементы вместо placeholder'а.** User отключил оффер → видит серый X. Лучше — что **сейчас на этой позиции** в тесте.
- ❌ **Сохранение idle-данных в running state.** Если в running должны быть live метрики — `idle`-данные («ещё не запущено») показывать **нельзя**.
- ❌ **Кнопки которые ничего не делают в текущем state.** «Запустить тест» доступна когда тест уже идёт — она должна быть **скрыта** или **превращена в «Стоп»**.
- ❌ **Statistics block пуст в running.** Тест идёт минуту — уже есть кликов 50, EPC 30₽. Это **уже** статистика. Должна быть на UI **немедленно**.

## Для product-architect

Добавить в 7+4 вопросов новый Q12:

**Q12 — Stateful UI lifecycle**

Если экран связан с процессом / объектом с состоянием:
- Перечислить все states
- Для каждого state — таблица (структура UI / данные / actions)
- Описать что показывается ВМЕСТО элементов которые были в idle
- Visual difference между states должен быть видимый с одного взгляда, не нюанс

## Для ui-design-architect

В разделе «Functional behavior» каждого компонента добавить:

```yaml
component: ExperimentDashboard
states:
  idle:
    structure: toolbar + history
    visible_elements: [run_button, params_form, prev_results_table]
    hidden_elements: [live_stats, current_variant_indicator]
  running:
    structure: live_section + rotation_with_placeholders + variants_table
    visible_elements: [live_stats, current_variant_indicator, variants_data_table, stop_button]
    hidden_elements: [run_button, params_form]
    placeholders:
      - in_rotation: 'для каждой тестовой позиции — placeholder с current variant + accumulated stats'
  completed:
    structure: result_summary + history_with_dates + apply_button
    visible_elements: [winner_card, lift_indicator, apply_button, restart_button]
    hidden_elements: [live_stats, stop_button, run_button]
```

## Для qa-scenario-tester

В Шаг 7 logical validation добавить sub-check **«State-driven UI»**:

После каждого действия меняющего state объекта (запустить тест → state = 'running'):
- Сравнить snapshot UI до и после
- **FAIL если** структура секции не изменилась (тот же layout, только бейдж добавился)
- **FAIL если** старые элементы (характерные для idle) всё ещё видны
- **FAIL если** новые элементы (live stats, placeholders) не появились

```js
// Псевдокод проверки
const before = snapshot('experiment-page', { state: 'idle' });
clickRunButton();
const after = snapshot('experiment-page', { state: 'running' });

assert(after.structure.sections !== before.structure.sections,
  'Структура UI не изменилась после запуска теста — нарушен lifecycle pattern');

assert(after.has('.live-stats') === true,
  'Live statistics секция не появилась в running state');

assert(after.has('.run-button') === false,
  'Run button всё ещё виден в running state');
```

## Связанные

- [[wiki/concepts/ab-experiment-product-thinking]] — domain knowledge А/Б
- [[wiki/concepts/component-reuse-discipline]] — one entity → one renderer
- `~/.claude/agents/product-architect.md` — Q12 stateful
- `~/.claude/agents/ui-design-architect.md` — functional behavior YAML с states
- `~/.claude/agents/qa-scenario-tester.md` — Шаг 7 state-driven assertions
