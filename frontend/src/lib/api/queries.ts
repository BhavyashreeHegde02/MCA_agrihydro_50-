"use client";

/**
 * React Query hooks over the typed client.
 *
 * Query keys are declared in one place so an invalidation after a mutation
 * cannot miss a cache entry by spelling its key differently. Creating a field,
 * for example, has to invalidate both that farm's field list and the farm
 * detail that carries its field count.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query";

import { api } from "./client";
import type {
  AdvisoryListResponse,
  CropDetail,
  CropOut,
  FarmCreate,
  FarmDetail,
  FarmOut,
  FarmUpdate,
  FarmerOut,
  FarmerUpdate,
  FieldCreate,
  FieldCropCreate,
  FieldCropDetail,
  FieldOut,
  FieldUpdate,
  GrowthStageOut,
  IrrigationCalculationOut,
  IrrigationCalculationRequest,
  IrrigationRecordCreate,
  IrrigationRecordOut,
  KcCurvePoint,
  PredictionOut,
  PredictionDetail,
  PredictionRequest,
  PredictionSummary,
  SoilDataCreate,
  SoilDataOut,
  WeatherOut,
  ExplanationOut,
  CoverageResponse,
  RainfallContextOut,
  WaterBudgetRequest,
  WaterBudgetResponse,
  WaterProductivityResponse,
} from "./types";

export const keys = {
  profile: ["farmer", "profile"] as const,
  farms: ["farms"] as const,
  farm: (id: number) => ["farms", id] as const,
  fields: (farmId: number) => ["farms", farmId, "fields"] as const,
  plantings: (fieldId: number) => ["fields", fieldId, "crops"] as const,
  allPlantings: (activeOnly: boolean) =>
    ["field-crops", { activeOnly }] as const,
  planting: (id: number) => ["field-crops", id] as const,
  soil: (fieldId: number) => ["fields", fieldId, "soil"] as const,
  crops: ["crops"] as const,
  crop: (id: number) => ["crops", id] as const,
  growthStages: (cropId: number) => ["crops", cropId, "stages"] as const,
  kcCurve: (cropId: number) => ["crops", cropId, "kc"] as const,
  history: (params: Record<string, unknown>) =>
    ["predictions", "history", params] as const,
  prediction: (id: number) => ["predictions", id] as const,
  explanation: (id: number) => ["predictions", id, "explanation"] as const,
  irrigationRecords: (fieldCropId?: number) =>
    ["irrigation", "records", { fieldCropId }] as const,
  advisory: ["advisory"] as const,
  weatherStatus: ["weather", "status"] as const,
  weatherCurrent: (location: object) =>
    ["weather", "current", location] as const,
  weatherForecast: (location: object, days: number) =>
    ["weather", "forecast", location, days] as const,
  analytics: (params: Record<string, unknown>) =>
    ["analytics", "cwr", params] as const,
  waterCoverage: ["water-intelligence", "coverage"] as const,
  waterProductivity: (params: Record<string, unknown>) =>
    ["water-intelligence", "productivity", params] as const,
  districtRainfall: (params: Record<string, unknown>) =>
    ["water-intelligence", "rainfall", params] as const,
};

type Options<T> = Omit<UseQueryOptions<T, Error, T>, "queryKey" | "queryFn">;

// ---------------------------------------------------------------------------
// Farmer, farms, fields
// ---------------------------------------------------------------------------

export function useProfile(options?: Options<FarmerOut>) {
  return useQuery({
    queryKey: keys.profile,
    queryFn: () => api.get<FarmerOut>("farmers/profile"),
    ...options,
  });
}

export function useUpdateProfile() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: FarmerUpdate) =>
      api.put<FarmerOut>("farmers/profile", body),
    onSuccess: (data) => client.setQueryData(keys.profile, data),
  });
}

export function useFarms(options?: Options<FarmOut[]>) {
  return useQuery({
    queryKey: keys.farms,
    queryFn: () => api.get<FarmOut[]>("farms"),
    ...options,
  });
}

export function useFarm(farmId: number, options?: Options<FarmDetail>) {
  return useQuery({
    queryKey: keys.farm(farmId),
    queryFn: () => api.get<FarmDetail>(`farms/${farmId}`),
    enabled: Number.isFinite(farmId) && farmId > 0,
    ...options,
  });
}

export function useCreateFarm() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: FarmCreate) => api.post<FarmOut>("farms", body),
    onSuccess: () => client.invalidateQueries({ queryKey: keys.farms }),
  });
}

export function useUpdateFarm(farmId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: FarmUpdate) => api.put<FarmOut>(`farms/${farmId}`, body),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: keys.farms });
      client.invalidateQueries({ queryKey: keys.farm(farmId) });
    },
  });
}

export function useDeleteFarm() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (farmId: number) => api.delete(`farms/${farmId}`),
    onSuccess: () => client.invalidateQueries({ queryKey: keys.farms }),
  });
}

export function useFields(farmId: number, options?: Options<FieldOut[]>) {
  return useQuery({
    queryKey: keys.fields(farmId),
    queryFn: () => api.get<FieldOut[]>(`farms/${farmId}/fields`),
    enabled: Number.isFinite(farmId) && farmId > 0,
    ...options,
  });
}

export function useCreateField(farmId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: FieldCreate) =>
      api.post<FieldOut>(`farms/${farmId}/fields`, body),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: keys.fields(farmId) });
      // The farm detail carries the field count and remaining area.
      client.invalidateQueries({ queryKey: keys.farm(farmId) });
    },
  });
}

export function useUpdateField(farmId: number, fieldId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: FieldUpdate) =>
      api.put<FieldOut>(`fields/${fieldId}`, body),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: keys.fields(farmId) });
      client.invalidateQueries({ queryKey: keys.farm(farmId) });
    },
  });
}

export function useDeleteField(farmId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (fieldId: number) => api.delete(`fields/${fieldId}`),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: keys.fields(farmId) });
      client.invalidateQueries({ queryKey: keys.farm(farmId) });
    },
  });
}

// ---------------------------------------------------------------------------
// Plantings and soil
// ---------------------------------------------------------------------------

export function usePlantings(
  fieldId: number,
  options?: Options<FieldCropDetail[]>,
) {
  return useQuery({
    queryKey: keys.plantings(fieldId),
    queryFn: () => api.get<FieldCropDetail[]>(`fields/${fieldId}/crops`),
    enabled: Number.isFinite(fieldId) && fieldId > 0,
    ...options,
  });
}

export function useAllPlantings(
  activeOnly = true,
  options?: Options<FieldCropDetail[]>,
) {
  return useQuery({
    queryKey: keys.allPlantings(activeOnly),
    queryFn: () =>
      api.get<FieldCropDetail[]>("field-crops", {
        query: { active_only: activeOnly },
      }),
    ...options,
  });
}

export function usePlanting(id: number, options?: Options<FieldCropDetail>) {
  return useQuery({
    queryKey: keys.planting(id),
    queryFn: () => api.get<FieldCropDetail>(`field-crops/${id}`),
    enabled: Number.isFinite(id) && id > 0,
    ...options,
  });
}

export function useCreatePlanting(fieldId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: FieldCropCreate) =>
      api.post<FieldCropDetail>(`fields/${fieldId}/crops`, body),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: keys.plantings(fieldId) });
      client.invalidateQueries({ queryKey: ["field-crops"] });
    },
  });
}

export function useSoil(fieldId: number, options?: Options<SoilDataOut[]>) {
  return useQuery({
    queryKey: keys.soil(fieldId),
    queryFn: () => api.get<SoilDataOut[]>(`fields/${fieldId}/soil-data`),
    enabled: Number.isFinite(fieldId) && fieldId > 0,
    ...options,
  });
}

export function useAddSoil(fieldId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: SoilDataCreate) =>
      api.post<SoilDataOut>(`fields/${fieldId}/soil-data`, body),
    onSuccess: () => client.invalidateQueries({ queryKey: keys.soil(fieldId) }),
  });
}

// ---------------------------------------------------------------------------
// Crop reference
// ---------------------------------------------------------------------------

export function useCrops(options?: Options<CropOut[]>) {
  return useQuery({
    queryKey: keys.crops,
    queryFn: () => api.get<CropOut[]>("crops"),
    // Reference data seeded at startup; it does not change while the app runs.
    staleTime: 30 * 60_000,
    ...options,
  });
}

export function useCrop(cropId: number, options?: Options<CropDetail>) {
  return useQuery({
    queryKey: keys.crop(cropId),
    queryFn: () => api.get<CropDetail>(`crops/${cropId}`),
    enabled: Number.isFinite(cropId) && cropId > 0,
    staleTime: 30 * 60_000,
    ...options,
  });
}

export function useGrowthStages(
  cropId: number,
  options?: Options<GrowthStageOut[]>,
) {
  return useQuery({
    queryKey: keys.growthStages(cropId),
    queryFn: () => api.get<GrowthStageOut[]>(`crops/${cropId}/growth-stages`),
    enabled: Number.isFinite(cropId) && cropId > 0,
    staleTime: 30 * 60_000,
    ...options,
  });
}

export function useKcCurve(cropId: number, options?: Options<KcCurvePoint[]>) {
  return useQuery({
    queryKey: keys.kcCurve(cropId),
    queryFn: () => api.get<KcCurvePoint[]>(`crops/${cropId}/kc-curve`),
    enabled: Number.isFinite(cropId) && cropId > 0,
    staleTime: 30 * 60_000,
    ...options,
  });
}

// ---------------------------------------------------------------------------
// Prediction
// ---------------------------------------------------------------------------

export function usePredict() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: PredictionRequest) =>
      api.post<PredictionOut>("predictions/cwr", body),
    onSuccess: () => {
      // A stored prediction changes the history, the advisory feed and the
      // analytics series at once.
      client.invalidateQueries({ queryKey: ["predictions"] });
      client.invalidateQueries({ queryKey: keys.advisory });
      client.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

export function useHistory(
  params: { field_crop_id?: number; start_date?: string; end_date?: string; limit?: number },
  options?: Options<PredictionSummary[]>,
) {
  return useQuery({
    queryKey: keys.history(params),
    queryFn: () =>
      api.get<PredictionSummary[]>("predictions/history", { query: params }),
    ...options,
  });
}

export function usePrediction(id: number, options?: Options<PredictionDetail>) {
  return useQuery({
    queryKey: keys.prediction(id),
    queryFn: () => api.get<PredictionDetail>(`predictions/${id}`),
    enabled: Number.isFinite(id) && id > 0,
    ...options,
  });
}

export function useExplanation(
  predictionId: number,
  options?: Options<ExplanationOut>,
) {
  return useQuery({
    queryKey: keys.explanation(predictionId),
    queryFn: () =>
      api.get<ExplanationOut>(`predictions/${predictionId}/explanation`),
    enabled: Number.isFinite(predictionId) && predictionId > 0,
    ...options,
  });
}

// ---------------------------------------------------------------------------
// Irrigation
// ---------------------------------------------------------------------------

export function useCalculateIrrigation() {
  return useMutation({
    mutationFn: (body: IrrigationCalculationRequest) =>
      api.post<IrrigationCalculationOut>("irrigation/calculate", body),
  });
}

export function useIrrigationRecords(
  fieldCropId?: number,
  options?: Options<IrrigationRecordOut[]>,
) {
  return useQuery({
    queryKey: keys.irrigationRecords(fieldCropId),
    queryFn: () =>
      api.get<IrrigationRecordOut[]>("irrigation/records", {
        query: { field_crop_id: fieldCropId },
      }),
    ...options,
  });
}

export function useLogIrrigation() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: IrrigationRecordCreate) =>
      api.post<IrrigationRecordOut>("irrigation/records", body),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["irrigation"] });
      client.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

// ---------------------------------------------------------------------------
// Advisory, weather, analytics
// ---------------------------------------------------------------------------

export function useAdvisory(options?: Options<AdvisoryListResponse>) {
  return useQuery({
    queryKey: keys.advisory,
    queryFn: () => api.get<AdvisoryListResponse>("advisory"),
    ...options,
  });
}

export function useWeatherStatus(options?: Options<WeatherStatus>) {
  return useQuery({
    queryKey: keys.weatherStatus,
    queryFn: () => api.get<WeatherStatus>("weather/status"),
    ...options,
  });
}

/**
 * The backend resolves a location from either an owned farm or explicit
 * coordinates, and returns 422 if it gets neither. The hooks stay disabled
 * until one of the two is available, so that 422 is never provoked.
 */
export interface WeatherLocation {
  farmId?: number;
  latitude?: number;
  longitude?: number;
}

function locationQuery(location: WeatherLocation) {
  return {
    farm_id: location.farmId,
    latitude: location.latitude,
    longitude: location.longitude,
  };
}

function hasLocation(location: WeatherLocation): boolean {
  return (
    location.farmId !== undefined ||
    (location.latitude !== undefined && location.longitude !== undefined)
  );
}

export function useCurrentWeather(
  location: WeatherLocation,
  options?: Options<WeatherOut>,
) {
  return useQuery({
    queryKey: keys.weatherCurrent(location),
    queryFn: () =>
      api.get<WeatherOut>("weather/current", { query: locationQuery(location) }),
    enabled: hasLocation(location),
    ...options,
  });
}

export function useWeatherForecast(
  location: WeatherLocation,
  days = 7,
  options?: Options<WeatherOut[]>,
) {
  return useQuery({
    queryKey: keys.weatherForecast(location, days),
    queryFn: () =>
      api.get<WeatherOut[]>("weather/forecast", {
        query: { ...locationQuery(location), days },
      }),
    enabled: hasLocation(location),
    ...options,
  });
}

// ---------------------------------------------------------------------------
// Water intelligence
// ---------------------------------------------------------------------------

export function useWaterCoverage(options?: Options<CoverageResponse>) {
  return useQuery({
    queryKey: keys.waterCoverage,
    queryFn: () => api.get<CoverageResponse>("water-intelligence/coverage"),
    // Source files do not change while the service runs.
    staleTime: 60 * 60_000,
    ...options,
  });
}

export function useWaterProductivity(
  params: { state?: string; district?: string } = {},
  options?: Options<WaterProductivityResponse>,
) {
  return useQuery({
    queryKey: keys.waterProductivity(params),
    queryFn: () =>
      api.get<WaterProductivityResponse>("water-intelligence/productivity", {
        query: params,
      }),
    staleTime: 30 * 60_000,
    ...options,
  });
}

export function useWaterBudget() {
  return useMutation({
    mutationFn: (body: WaterBudgetRequest) =>
      api.post<WaterBudgetResponse>("water-intelligence/water-budget", body),
  });
}

export function useDistrictRainfall(
  params: { farm_id?: number; state?: string; district?: string },
  options?: Options<RainfallContextOut>,
) {
  return useQuery({
    queryKey: keys.districtRainfall(params),
    queryFn: () =>
      api.get<RainfallContextOut>("water-intelligence/rainfall", {
        query: params,
      }),
    enabled:
      params.farm_id !== undefined ||
      (Boolean(params.state) && Boolean(params.district)),
    ...options,
  });
}

/** `analytics.weather_status` — GET /api/v1/weather/status, an untyped dict. */
export interface WeatherStatus {
  provider: string;
  configured: boolean;
  note?: string;
  [key: string]: unknown;
}
