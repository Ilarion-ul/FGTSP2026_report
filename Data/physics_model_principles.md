# KSA_TargetSim: детальний опис фізичної моделі, принципів і формул

> Стан проєкту перевірено по поточному HEAD гілки (див. `git log`).
> Документ описує **саме реалізовану** в коді модель Geant4, а не бажану/планову.

---

## 1. Область застосування моделі

KSA_TargetSim моделює ланцюжок взаємодій в мішені типу W-Ta / U-Mo / U-Al:

\[
 e^- \rightarrow \gamma \rightarrow (\gamma,n) \rightarrow n
\]

Основна ідея: генерується первинний електронний пучок, далі Geant4 рахує всі вторинні процеси,
а код проєкту виконує скоринг енерговиділення, виходів нейтронів/фотонів, NIEL-proxy та газоутворення
(H/He) на рівні пластин і сіток.

---

## 2. Фізичний стек Geant4, що використовується

### 2.1 Physics list

Фізика ініціалізується через `G4PhysListFactory` і reference list з конфіга.
За замовчуванням використовується:

- `QGSP_BIC_HPT`

Якщо в конфігу вказано невідомий список, система робить fallback на `QGSP_BIC_HPT`.

### 2.2 Production cut

Додатково задається `default cut` у мм (`cut_mm`) через:

\[
\text{cut} = cut\_mm \cdot \text{mm}
\]

Це впливає на пороги генерації вторинних частинок у Geant4.

### 2.3 Важливе уточнення

Поле `enablePhotonuclear` наразі є в конфігу, але в коді як окремий перемикач physics-конструкторів
ще не задіяне (позначено як placeholder).

---

## 3. Первинний пучок: математична модель генератора

Первинка задається в `PrimaryGeneratorAction` (1 електрон на подію).

### 3.1 Енергія первинного електрона

Центральна енергія: \(E_0\) (`beam.energy_MeV`).

- Для `gauss`:
\[
\delta \sim \mathcal{N}(0,\sigma_{rel}), \quad E = E_0(1+\delta)
\]
- Для `uniform`:
\[
\delta \sim \mathcal{U}(-\Delta,+\Delta), \quad E = E_0(1+\delta)
\]

де:
- \(\sigma_{rel} = \text{energy\_sigma\_rel\_1sigma}\)
- \(\Delta = \text{energy\_uniform\_rel\_halfspan}\)

Мінімальне обмеження в коді:
\[
E \ge 10^{-6}\;\text{MeV}
\]

### 3.2 Просторовий профіль пучка

Координати старту:
\[
x \sim \mathcal{N}(0,\sigma_x), \quad y \sim \mathcal{N}(0,\sigma_y), \quad z=z_0
\]
з подальшим зміщенням на `position_mm`.

Дефекти:
- `offset`: додає \(\Delta x,\Delta y\)
- `halo`: з імовірністю `halo_fraction` множить \(\sigma_x,\sigma_y\) на `halo_sigma_scale`

### 3.3 Кутовий розкид

Компоненти напрямку:
\[
d_x = d_{x0} + \mathcal{N}(0,\sigma_{\theta x}),\quad d_y = d_{y0} + \mathcal{N}(0,\sigma_{\theta y}),\quad d_z=d_{z0}
\]

де \(\sigma_{\theta}\) задаються в mrad та переводяться в rad.
Після цього вектор нормується:
\[
\vec d \leftarrow \frac{\vec d}{\|\vec d\|}
\]

Для `tilt` додаються систематичні кути `tilt_mrad`.

### 3.4 Емітансний режим (опціонально)

Якщо `use_emit_model=true`:
\[
\gamma = 1 + \frac{E_0}{m_ec^2}, \quad \beta = \sqrt{1-\frac{1}{\gamma^2}}, \quad
\varepsilon_{geom} = \frac{\varepsilon_n}{\beta\gamma}
\]

Далі оцінюються:
\[
\sigma_{\theta x} \approx \frac{\varepsilon_{geom}}{\sigma_x}, \quad
\sigma_{\theta y} \approx \frac{\varepsilon_{geom}}{\sigma_y}
\]

(наближення без повної Twiss-транспортної моделі).

---

## 4. Геометричний контекст скорингу

Скоринг виконується в `SteppingAction` для plate-об’ємів:

- W-Ta: `TargetSubstrate*`, `TargetCoating*`, `TargetBufferTi*`
- U-Mo: `PlateU_*`, `PlateCladAl_*`

Для кожного кроку в plate-об’ємах акумулюються:
- `edep` (total energy deposit)
- довжина кроку нейтрона
- NIEL-proxy
- H/He (через вторинні частинки)
- заповнення 3D/2D карт

---

## 5. Скорингові величини та формули

## 5.1 Енерговиділення

На кожному кроці:
\[
E_{dep}^{run} = \sum_{steps} E_{dep}^{step}
\]

Агрегується:
- окремо по `substrate`/`coating`
- по пластинах `plate_edep_MeV[i]`
- у 3D-сітці `edep_3d(ix,iy,iz)`

## 5.2 Лічильники частинок (унікальні треки)

Для gamma і neutron використовується унікалізація за `trackID` в межах події:
\[
N_{\gamma,event} = |\{trackID_{\gamma}\}|,\quad
N_{n,event} = |\{trackID_n\}|
\]

Потім сумується по подіях.

## 5.3 `nNeutronExit`

Рахується, коли нейтрон іде з plate-volume в non-plate-volume
(теж з унікалізацією по `trackID` на подію).

> Важливо: це не завжди дорівнює «витік з усієї мішені назовні»,
> а радше «вихід з пластинної частини моделі».

## 5.4 Surface-hit дані нейтронів/фотонів

Логується перетин меж target-bounds (`preInside && !postInside`) з класифікацією поверхні:
- downstream / upstream / side_x / side_y

Пишеться в ROOT-дерева `NeutronSurf` та `PhotonSurf`.

## 5.5 NIEL proxy (damage proxy)

Використовується Geant4-оцінка неіонізуючого внеску кроку:
\[
E_{NIEL}^{run,plate} = \sum_{steps\in plate} E_{nonion}^{step}
\]

У виході зараз це **per-plate** значення (MeV), а не воксельне DPA-поле.

## 5.6 Газоутворення H/He (proxy)

По вторинних частинках у кроці:
- H-група: proton, deuteron, triton
- He-група: alpha, He3

Агрегація робиться з урахуванням `secondary->GetWeight()`.

---

## 6. Нормування, одиниці, перерахунок режиму

### 6.1 Що є в моделі зараз

- Базова інтерпретація результатів: **per primary electron**.
- У `RunMeta` зберігаються `nEvents`, `per_primary=1.0`, `N_e_per_s`.

Формула:
\[
N_{e/s}=\frac{I_{avg}}{e}
\]

### 6.2 Перехід до фізичного режиму

Для будь-якої величини \(Q_{pp}\) (per-primary):
\[
Q_{rate}=Q_{pp}\cdot N_{e/s}, \qquad
Q_{campaign}=Q_{pp}\cdot N_e, \quad N_e=\frac{I}{e}t
\]

---

## 7. Формати виходу (фактично реалізовані)

### 7.1 ROOT (`KSA_USE_ROOT=ON`)

- `run_summary` (TTree): інтегральні метрики
- `RunMeta` (TTree): параметри пучка/геометрії + нормування
- `NeutronSurf`, `PhotonSurf` (TTree): surface crossings
- `edep_3d` (TH3D)
- `h2_edep_xy_mid`, `plate_neutron_heatmap_*`
- `h1_niel_plate`, `h1_gas_h_plate`, `h1_gas_he_plate`

### 7.2 Non-ROOT

- `results/logs/run_summary.json`
- `results/logs/heatmaps.json`

---

## 8. Ключові числові результати з Geant4 (що саме порівнюємо між матеріалами мішені)

Нижче перелік KPI, які коректно порівнювати між W-Ta, U-Mo, U-Al
(за однакових `nEvents`, енергії та налаштувань пучка).

## 8.1 Нейтронні KPI

1. \(nNeutron/nEvents\) — вихід нейтронів на первинний електрон (внутрішній production KPI).
2. `NeutronSurf entries / nEvents` і `weighted / nEvents` — вихід через межі target-bounds.
3. Розподіл по поверхнях (`downstream/upstream/side`) — напрямний витік.
4. Спектральні характеристики `En` (лінійний/лог діапазони з export-макроса).

## 8.2 Енергетичні KPI

1. `edep_substrate` та `edep_coating` (MeV/run, далі /nEvents).
2. `plate_edep_MeV[i]/nEvents` — профіль теплового навантаження по пластинах.
3. `edep_3d` (локалізація піків у 3D, hotspot-аналіз).

## 8.3 Пошкодження/матеріалознавчі KPI

1. `h1_niel_plate[i]/nEvents` — damage proxy per plate.
2. `h1_gas_h_plate[i]/nEvents`, `h1_gas_he_plate[i]/nEvents` — газоутворення.

## 8.4 Метрики якості порівняння

Для чесного material-to-material порівняння в таблицях/графіках тримати однаковими:
- physics list;
- beam energy/spread;
- nEvents;
- геометричні межі скорингу.

---

## 9. Обмеження поточної моделі

1. Немає воксельного `DPA(x)` або `damage_energy(x)` у стандартному output.
2. Немає `\phi_n(E,x)` по energy groups у вокселях.
3. `nNeutronExit` не тотожний «витік назовні всієї збірки» — це plate-exit KPI.
4. `enablePhotonuclear` як окремий runtime toggle поки не задіяний у фабриці physics list.

---

## 10. Рекомендований порядок розширення моделі

1. Додати `MeshData` (voxel table) з `voxel_id/material_id/volume_id`.
2. Перенести NIEL з per-plate у per-voxel `damage_energy_eV_per_primary`.
3. Додати груповий нейтронний флюенс `flux_g0..flux_gN` у тих самих вокселях.
4. Додати в non-ROOT: `run_meta.json`, `mesh_definition.json`, `mesh_data.csv`.
5. Зробити валідаційні sanity-check:
   - сума по вокселях = інтегральним метрикам,
   - адекватність per-primary масштабування.