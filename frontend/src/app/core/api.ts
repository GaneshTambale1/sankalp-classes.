import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { environment } from '../../environments/environment';
export interface PageResponse {items:any[]; total:number; page:number; size:number}
export interface Meta {classes:any[];batches:any[];subjects:any[];teachers:any[];students:any[];examinations:any[]}
@Injectable({providedIn:'root'})
export class ApiService {
  private http=inject(HttpClient);
  get<T>(path:string, params?:Record<string,string|number|undefined>) {
    let p=new HttpParams();for (const [key,value] of Object.entries(params||{})){if (value!==undefined && value!=='')p=p.set(key,String(value));}
    return this.http.get<T>(`${environment.apiUrl}/${path}`,{params:p});
  }
  post<T>(path:string,payload:unknown){return this.http.post<T>(`${environment.apiUrl}/${path}`,payload);}
  put<T>(path:string,payload:unknown){return this.http.put<T>(`${environment.apiUrl}/${path}`,payload);}
  delete<T>(path:string){return this.http.delete<T>(`${environment.apiUrl}/${path}`);}
  blob(path:string,params?:Record<string,string|number|undefined>){
    let p=new HttpParams();for(const [k,v] of Object.entries(params||{}))if(v!==undefined&&v!=='')p=p.set(k,String(v));
    return this.http.get(`${environment.apiUrl}/${path}`,{params:p,responseType:'blob'});
  }
}
export function downloadBlob(data:Blob,name:string):void {const url=URL.createObjectURL(data);const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
export function readableError(err:any):string {return err?.error?.error || err?.message || 'Request failed. Please try again.';}
