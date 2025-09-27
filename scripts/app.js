const SCENARIOS = {
  bull: {
    cagr: 50,
    duration: 3,
    exposure: 90,
    techAllocation: 100,
    breakdown: {
      robotics: 50,
      semiconductors: 40,
      software: 10
    },
    description:
      '高速成长阶段，以机器人为核心主线，半导体与软件协同放大弹性。'
  },
  bear: {
    cagr: 15,
    duration: 3,
    exposure: 30,
    techAllocation: 20,
    breakdown: {
      robotics: 10,
      semiconductors: 80,
      software: 10
    },
    description:
      '防守状态下聚焦核心确定性资产，压缩仓位并保持科技底仓以等待反转。'
  }
};

function cloneScenario(data) {
  return {
    cagr: data.cagr,
    duration: data.duration,
    exposure: data.exposure,
    techAllocation: data.techAllocation,
    breakdown: { ...data.breakdown },
    description: data.description
  };
}

const state = {
  bull: cloneScenario(SCENARIOS.bull),
  bear: cloneScenario(SCENARIOS.bear)
};

const targetCagrEl = document.querySelector('#target-cagr');
const investmentDurationEl = document.querySelector('#investment-duration-display');
const targetExposureEl = document.querySelector('#target-exposure');
const techAllocationEl = document.querySelector('#tech-allocation');
const techBreakdownEl = document.querySelector('#tech-breakdown');
const scenarioButtons = document.querySelectorAll('.scenario-button');

const cagrSlider = document.querySelector('#cagr-slider');
const cagrOutput = document.querySelector('#cagr-slider-output');
const durationSlider = document.querySelector('#duration-slider');
const durationOutput = document.querySelector('#duration-slider-output');
const exposureSlider = document.querySelector('#exposure-slider');
const exposureOutput = document.querySelector('#exposure-slider-output');
const techWeightSlider = document.querySelector('#tech-weight-slider');
const techWeightOutput = document.querySelector('#tech-weight-output');
const roboticsSlider = document.querySelector('#robotics-slider');
const roboticsOutput = document.querySelector('#robotics-output');
const semiconductorSlider = document.querySelector('#semiconductor-slider');
const semiconductorOutput = document.querySelector('#semiconductor-output');
const softwareOutput = document.querySelector('#software-output');
const growthChart = document.querySelector('#growth-chart');
const growthLine = growthChart ? growthChart.querySelector('[data-role="line"]') : null;
const growthArea = growthChart ? growthChart.querySelector('[data-role="area"]') : null;
const growthEndValue = document.querySelector('#growth-end-value');

const scenarioDescription = document.createElement('p');
scenarioDescription.className = 'scenario-description';
scenarioDescription.textContent = SCENARIOS.bull.description;

const objectivesBody = document.querySelector('#objectives-card .card__body');
if (objectivesBody) {
  objectivesBody.appendChild(scenarioDescription);
}

let activeScenario = 'bull';

function formatPercent(value) {
  return `${Math.round(value)}%`;
}

function formatYears(value) {
  return `${value}年`;
}

function updateBreakdownView(breakdown) {
  const robotics = Math.round(breakdown.robotics);
  const semiconductors = Math.round(breakdown.semiconductors);
  const software = Math.max(0, 100 - robotics - semiconductors);

  roboticsOutput.textContent = formatPercent(robotics);
  semiconductorOutput.textContent = formatPercent(semiconductors);
  softwareOutput.textContent = formatPercent(software);
  techBreakdownEl.textContent = `机器人${robotics}% / 半导体${semiconductors}% / 软件${software}%`;
}

function clampBreakdown() {
  let robotics = Number(roboticsSlider.value);
  let semiconductors = Number(semiconductorSlider.value);

  if (robotics > 100 - semiconductors) {
    robotics = 100 - semiconductors;
    roboticsSlider.value = robotics;
  }

  if (semiconductors > 100 - robotics) {
    semiconductors = 100 - robotics;
    semiconductorSlider.value = semiconductors;
  }

  roboticsSlider.max = 100 - semiconductors;
  semiconductorSlider.max = 100 - robotics;

  const software = Math.max(0, 100 - robotics - semiconductors);

  state[activeScenario].breakdown = {
    robotics,
    semiconductors,
    software
  };

  updateBreakdownView(state[activeScenario].breakdown);
}

function updateGrowthChart() {
  if (!growthChart || !growthLine || !growthArea || !growthEndValue) {
    return;
  }

  const { cagr, duration } = state[activeScenario];
  const years = Math.max(1, duration);
  const rate = Math.max(0, cagr) / 100;
  const baseCapital = 100;
  const width = 280;
  const height = 160;
  const paddingTop = 16;
  const paddingBottom = 20;
  const usableHeight = height - paddingTop - paddingBottom;
  const steps = Math.max(12, years * 12);
  const finalValue = baseCapital * Math.pow(1 + rate, years);
  const maxValue = Math.max(baseCapital, finalValue);

  const points = [];
  for (let i = 0; i <= steps; i += 1) {
    const ratio = i / steps;
    const time = ratio * years;
    const amount = baseCapital * Math.pow(1 + rate, time);
    const x = ratio * width;
    const normalised = maxValue === baseCapital ? 0 : (amount - baseCapital) / (maxValue - baseCapital);
    const y = height - paddingBottom - normalised * usableHeight;
    points.push({ x, y });
  }

  let linePath = '';
  points.forEach((point, index) => {
    const command = index === 0 ? 'M' : 'L';
    linePath += `${command}${point.x.toFixed(2)} ${point.y.toFixed(2)} `;
  });

  const baseline = height - paddingBottom;
  let areaPath = `M0 ${baseline.toFixed(2)} `;
  points.forEach((point) => {
    areaPath += `L${point.x.toFixed(2)} ${point.y.toFixed(2)} `;
  });
  areaPath += `L${width.toFixed(2)} ${baseline.toFixed(2)} Z`;

  growthLine.setAttribute('d', linePath.trim());
  growthArea.setAttribute('d', areaPath.trim());
  growthEndValue.textContent = finalValue.toFixed(1);
}

function applyScenario(mode) {
  activeScenario = mode;
  const data = state[mode];

  targetCagrEl.textContent = formatPercent(data.cagr);
  investmentDurationEl.textContent = formatYears(data.duration);
  targetExposureEl.textContent = formatPercent(data.exposure);
  techAllocationEl.textContent = formatPercent(data.techAllocation);
  updateBreakdownView(data.breakdown);

  cagrSlider.value = data.cagr;
  cagrOutput.textContent = formatPercent(data.cagr);
  durationSlider.value = data.duration;
  durationOutput.textContent = formatYears(data.duration);
  exposureSlider.value = data.exposure;
  exposureOutput.textContent = formatPercent(data.exposure);
  techWeightSlider.value = data.techAllocation;
  techWeightOutput.textContent = formatPercent(data.techAllocation);
  roboticsSlider.value = data.breakdown.robotics;
  semiconductorSlider.value = data.breakdown.semiconductors;

  clampBreakdown();

  scenarioDescription.textContent = data.description;

  updateGrowthChart();

  scenarioButtons.forEach((btn) => {
    btn.classList.toggle('is-active', btn.dataset.scenario === mode);
  });
}

scenarioButtons.forEach((button) => {
  button.addEventListener('click', () => applyScenario(button.dataset.scenario));
});

cagrSlider.addEventListener('input', () => {
  const value = Number(cagrSlider.value);
  state[activeScenario].cagr = value;
  targetCagrEl.textContent = formatPercent(value);
  cagrOutput.textContent = formatPercent(value);
  updateGrowthChart();
});

durationSlider.addEventListener('input', () => {
  const value = Number(durationSlider.value);
  state[activeScenario].duration = value;
  investmentDurationEl.textContent = formatYears(value);
  durationOutput.textContent = formatYears(value);
  updateGrowthChart();
});

exposureSlider.addEventListener('input', () => {
  const value = Number(exposureSlider.value);
  state[activeScenario].exposure = value;
  targetExposureEl.textContent = formatPercent(value);
  exposureOutput.textContent = formatPercent(value);
});

techWeightSlider.addEventListener('input', () => {
  const value = Number(techWeightSlider.value);
  state[activeScenario].techAllocation = value;
  techAllocationEl.textContent = formatPercent(value);
  techWeightOutput.textContent = formatPercent(value);
});

roboticsSlider.addEventListener('input', () => {
  clampBreakdown();
});

semiconductorSlider.addEventListener('input', () => {
  clampBreakdown();
});

const prefersDark =
  window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)');
const body = document.body;

function updateTheme() {
  if (prefersDark.matches) {
    body.classList.add('dark');
  } else {
    body.classList.remove('dark');
  }
}

if (prefersDark) {
  prefersDark.addEventListener('change', updateTheme);
  updateTheme();
}

applyScenario(activeScenario);
