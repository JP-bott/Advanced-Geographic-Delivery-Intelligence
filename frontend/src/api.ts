import type {Filters} from './types'
export function query(filters:Filters, extra:Record<string,string|number|undefined>={}) {
  const params = new URLSearchParams()
  for(const [key,value] of Object.entries({...filters,...extra})) if(value!==''&&value!==undefined) params.set(key,String(value))
  return params.toString()
}
export async function getJson<T>(path:string,signal?:AbortSignal):Promise<T> {
  const response=await fetch(path,{signal})
  if(!response.ok) {let msg=`Request failed (${response.status})`;try{const e=await response.json();msg=e.detail||msg}catch{/* no payload */}throw new Error(msg)}
  return response.json() as Promise<T>
}
export const num=(n:number|null|undefined,d=0)=>n==null?'—':Number(n).toLocaleString('en-PH',{minimumFractionDigits:d,maximumFractionDigits:d})
export const percentage=(n:number|null|undefined)=>n==null?'—':`${num(n,1)}%`
export const php=(n:number|null|undefined)=>n==null?'—':`₱${num(n,0)}`
export const shortDate=(value?:string|null)=>value?value.slice(0,10):'—'
