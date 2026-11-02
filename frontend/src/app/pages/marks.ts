import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService, Meta, PageResponse, readableError } from '../core/api';
interface MarkRow {student_id:number;name:string;code:string;obtained:number|null;remarks:string}
@Component({standalone:true,imports:[CommonModule,FormsModule],template:`
<div class="page-heading"><div><span class="eyebrow">EXAMINATION MANAGEMENT</span><h1>Marks Entry</h1><p>Enter and validate marks for your assigned examinations and subjects.</p></div></div>
@if(message()){<div class="alert" [class.alert-danger]="failed()" [class.alert-success]="!failed()">{{message()}}</div>}
<div class="panel filters-panel"><div class="filter-grid"><div><label class="form-label">Examination</label><select class="form-select" [(ngModel)]="examId" (ngModelChange)="examChanged()"><option [ngValue]="0">Select exam</option>@for(e of meta().examinations;track e.id){<option [ngValue]="e.id">{{e.name}}</option>}</select></div><div><label class="form-label">Subject</label><select class="form-select" [(ngModel)]="subjectId" (ngModelChange)="load()"><option [ngValue]="0">Select subject</option>@for(s of subjects();track s.id){<option [ngValue]="s.id">{{s.name}}</option>}</select></div><div class="filter-action"><button class="btn btn-outline-primary" (click)="load()" [disabled]="!examId||!subjectId">Load Students</button></div></div></div>
<div class="panel"><div class="panel-heading"><div><h3>Bulk Marks Entry</h3><small>@if(selectedConfig()){Maximum {{selectedConfig().max_marks}} · Passing {{selectedConfig().passing_marks}}}@else{Choose an examination and subject}</small></div><button class="btn btn-primary" (click)="save()" [disabled]="busy()||!rows().length">{{busy()?'Saving…':'Save Marks'}}</button></div>
<div class="table-responsive"><table class="table modern-table"><thead><tr><th>Student</th><th>Student ID</th><th>Obtained Marks</th><th>Remarks</th></tr></thead><tbody>@for(r of rows();track r.student_id){<tr><td><strong>{{r.name}}</strong></td><td>{{r.code}}</td><td><input class="form-control marks-input" type="number" min="0" [max]="selectedConfig()?.max_marks" step="0.01" [(ngModel)]="r.obtained"></td><td><input class="form-control" type="text" [(ngModel)]="r.remarks" placeholder="Optional"></td></tr>}</tbody></table></div>
@if(!rows().length){<div class="empty-state">Select an exam and subject to begin. Configure exam subjects before entering marks.</div>}</div>
`})
export class MarksPage implements OnInit{
 private api=inject(ApiService);meta=signal<Meta>({classes:[],batches:[],subjects:[],teachers:[],students:[],examinations:[]}); configs=signal<any[]>([]);rows=signal<MarkRow[]>([]);
 examId=0;subjectId=0;busy=signal(false);message=signal('');failed=signal(false);
 ngOnInit(){this.api.get<Meta>('meta').subscribe({next:r=>this.meta.set(r)});this.api.get<PageResponse>('examination-subjects',{size:100}).subscribe({next:r=>this.configs.set(r.items)});}
 subjects(){const ids=new Set(this.configs().filter(c=>c.examination_id===this.examId).map(c=>c.subject_id));return this.meta().subjects.filter(s=>ids.has(s.id));}
 selectedConfig(){return this.configs().find(c=>c.examination_id===this.examId && c.subject_id===this.subjectId);}
 examChanged(){this.subjectId=0;this.rows.set([]);}
 notice(msg:string,failed=false){this.message.set(msg);this.failed.set(failed);}
 load(){this.rows.set([]);if(!this.examId||!this.subjectId)return;const exam=this.meta().examinations.find(e=>e.id===this.examId);if(!exam)return;
   const students=this.meta().students.filter(s=>s.class_id===exam.class_id && (!exam.batch_id||exam.batch_id===s.batch_id));
   this.api.get<any>('marks',{examination_id:this.examId,subject_id:this.subjectId}).subscribe({next:r=>{
     const existing=new Map<number,any>(r.items.map((m:any)=>[m.student_id,m]));
     this.rows.set(students.map(s=>({student_id:s.id,name:s.name,code:s.code,obtained:existing.get(s.id)?.obtained??null,remarks:existing.get(s.id)?.remarks||''})));
   },error:e=>this.notice(readableError(e),true)});
 }
 save(){const filled=this.rows().filter(r=>r.obtained!==null&&r.obtained!==undefined);
  if(!filled.length){this.notice('Enter at least one mark',true);return;}
  const max=this.selectedConfig()?.max_marks;
  if(filled.some(r=>Number(r.obtained)<0||Number(r.obtained)>max||!Number.isFinite(Number(r.obtained)))){this.notice(`Marks must be between 0 and ${max}`,true);return;}
  this.busy.set(true);this.api.post<any>('marks/bulk',{examination_id:this.examId,subject_id:this.subjectId,records:filled.map(r=>({student_id:r.student_id,obtained:r.obtained,remarks:r.remarks}))}).subscribe({next:r=>{this.busy.set(false);this.notice(`Saved marks for ${r.saved} students`);},error:e=>{this.busy.set(false);this.notice(readableError(e),true);}});
 }
}
