import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService, readableError } from '../core/api';
@Component({standalone:true,imports:[CommonModule,FormsModule],template:`
<div class="page-heading"><div><span class="eyebrow">CONFIGURATION</span><h1>Institute Settings</h1><p>Personalize your institute information and academic grading system.</p></div><button class="btn btn-primary" (click)="save()" [disabled]="busy()">{{busy()?'Saving…':'Save Settings'}}</button></div>
@if(message()){<div class="alert" [class.alert-danger]="failed()" [class.alert-success]="!failed()">{{message()}}</div>}
<div class="grid-two"><section class="panel"><h3>General Information</h3><p class="muted">Institute details and academic preferences</p>@for(key of keys;track key){<div class="mb-3"><label class="form-label">{{label(key)}}</label><input class="form-control" [(ngModel)]="items[key]"></div>}</section><section class="panel"><h3>Grade Configuration</h3><p class="muted">Each grade applies from its minimum percentage up to the next higher threshold.</p>@for(g of grades;track $index){<div class="grade-line"><input type="number" min="0" max="100" class="form-control" [(ngModel)]="g.min_percentage"><input type="text" class="form-control" [(ngModel)]="g.grade"></div>}<button class="btn btn-outline-primary btn-sm mt-3" (click)="grades.push({min_percentage:0,grade:''})">Add Grade Range</button></section></div>
`})
export class SettingsPage implements OnInit{
 private api=inject(ApiService);items:Record<string,string>={};grades:any[]=[];busy=signal(false);message=signal('');failed=signal(false);
 keys=['institute_name','institute_address','contact_number','email','academic_year','attendance_warning_threshold','timezone','date_format'];
 label(key:string){return key.replaceAll('_',' ').replace(/\b\w/g,s=>s.toUpperCase());}
 ngOnInit(){this.api.get<any>('settings').subscribe({next:r=>{this.items=r.items;this.grades=r.grades.map((g:any)=>({min_percentage:g.min_percentage,grade:g.grade}));},error:e=>{this.message.set(readableError(e));this.failed.set(true);}});}
 save(){this.busy.set(true);this.api.put<any>('settings',{items:this.items,grades:this.grades}).subscribe({next:()=>{this.busy.set(false);this.message.set('Settings saved successfully');this.failed.set(false);},error:e=>{this.busy.set(false);this.message.set(readableError(e));this.failed.set(true);}});}
}
