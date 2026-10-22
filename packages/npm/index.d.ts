export interface ZipRecord {
  zip: string;
  city: string;
  state: string;
  county: string;
  population: number;
  timezone: string;
}
export interface Facility {
  name: string;
  city: string;
  state: string;
  rating: string;
  url: string;
}
export interface Place {
  name: string;
  state: string;
  county: string;
  population: number;
  url: string;
}
export interface College {
  name: string;
  city: string;
  state: string;
  unitid: number;
  url: string;
}
export interface Airport {
  iata: string;
  ident: string;
  icao: string;
  name: string;
  city: string;
  country: string;
}
export interface AreaCode {
  code: string;
  label: string;
  url: string;
}
export interface IfscBranch {
  ifsc: string;
  branch: string;
  district: string;
  state: string;
}

export function zipCode(zip: string): Promise<ZipRecord | null>;
export function hospitals(query: string, limit?: number): Promise<Facility[]>;
export function nursingHomes(query: string, limit?: number): Promise<Facility[]>;
export function homeHealth(query: string, limit?: number): Promise<Facility[]>;
export function dialysis(query: string, limit?: number): Promise<Facility[]>;
export function colleges(query: string, limit?: number): Promise<College[]>;
export function places(query: string, limit?: number): Promise<Place[]>;
export function airports(query: string, limit?: number): Promise<Airport[]>;
export function areaCodes(query: string, limit?: number): Promise<AreaCode[]>;
export function ifscBank(bank: string): Promise<IfscBranch[]>;
export const endpoints: Record<string, string | ((arg: string) => string)>;
