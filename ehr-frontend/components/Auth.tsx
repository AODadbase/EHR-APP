import React, { useState, useEffect } from 'react';
import { Activity, ArrowRight, Lock, User, Mail, Building, Check, X } from 'lucide-react';
import { authService } from '../services/authService';
import { User as UserType } from '../types';

interface AuthProps {
  onLogin: (user: UserType) => void;
}

const Auth: React.FC<AuthProps> = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [step, setStep] = useState<'details' | 'verification'>('details');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [generatedCode, setGeneratedCode] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    name: '',
    username: '',
    password: '',
    confirmPassword: '',
    email: '',
    organization: '',
    verificationCode: ''
  });

  // Validation State
  const [usernameError, setUsernameError] = useState('');
  const [passwordCriteria, setPasswordCriteria] = useState({
    length: false,
    upper: false,
    lower: false,
    number: false
  });
  const [passwordsMatch, setPasswordsMatch] = useState(true);

  // Real-time validation effects
  useEffect(() => {
    if (isLogin) return;

    // Password Criteria Check
    const pwd = formData.password;
    setPasswordCriteria({
        length: pwd.length >= 8,
        upper: /[A-Z]/.test(pwd),
        lower: /[a-z]/.test(pwd),
        number: /[0-9]/.test(pwd)
    });

    // Match Check
    setPasswordsMatch(formData.password === formData.confirmPassword || formData.confirmPassword === '');
  }, [formData.password, formData.confirmPassword, isLogin]);

  useEffect(() => {
    if (isLogin) {
        setUsernameError('');
        return;
    }
    // Username Validation
    const u = formData.username;
    if (!u) {
        setUsernameError('');
        return;
    }

    const isAlphanumeric = /^[a-zA-Z0-9]+$/.test(u);
    const hasLetter = /[a-zA-Z]/.test(u);
    const isValidLength = u.length > 5;

    if (!isAlphanumeric) {
        setUsernameError('Only English letters and numbers allowed.');
    } else if (!hasLetter) {
        setUsernameError('Must contain at least one letter.');
    } else if (!isValidLength) {
        setUsernameError('Must be longer than 5 characters.');
    } else {
        setUsernameError('');
    }
  }, [formData.username, isLogin]);

  const handleSendCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    // Detailed Validation
    if (usernameError) {
        setError(`Username Error: ${usernameError}`);
        return;
    }
    
    const { length, upper, lower, number } = passwordCriteria;
    if (!length || !upper || !lower || !number) {
        setError("Password does not meet security requirements.");
        return;
    }

    if (formData.password !== formData.confirmPassword) {
        setError("Passwords do not match.");
        return;
    }

    if (!formData.name || !formData.email || !formData.organization) {
        setError("All fields are required.");
        return;
    }
    if (!formData.email.includes('@')) {
        setError("Please enter a valid email address.");
        return;
    }

    setLoading(true);
    try {
        const code = await authService.sendVerificationCode(formData.email);
        setGeneratedCode(code);
        setStep('verification');
    } catch (err: any) {
        setError(err.message || 'Failed to send verification code.');
    } finally {
        setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (formData.verificationCode !== generatedCode) {
        setError("Invalid verification code. Please check your email.");
        return;
    }

    setLoading(true);
    try {
        const user = await authService.register({
            username: formData.username,
            password: formData.password,
            name: formData.name,
            email: formData.email,
            organization: formData.organization
        });
        onLogin(user);
    } catch (err: any) {
        setError(err.message);
    } finally {
        setLoading(false);
    }
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      setError('');
      setLoading(true);
      try {
        const user = await authService.login(formData.username, formData.password);
        onLogin(user);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
  };

  const toggleMode = () => {
      setIsLogin(!isLogin);
      setError('');
      setStep('details');
      setGeneratedCode(null);
      setFormData({ ...formData, password: '', confirmPassword: '' });
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl overflow-hidden flex max-w-5xl w-full border border-slate-200">
        
        {/* Left Side - Brand / Decorative */}
        <div className="hidden md:flex flex-col justify-between w-5/12 bg-slate-900 p-12 text-white relative overflow-hidden">
           {/* Abstract Pattern */}
           <div className="absolute top-0 right-0 w-64 h-64 bg-brand-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
           <div className="absolute bottom-0 left-0 w-64 h-64 bg-blue-600/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2"></div>

           <div>
              <div className="flex items-center gap-3 mb-8">
                <div className="p-2 bg-brand-600 rounded-lg">
                  <Activity className="h-6 w-6 text-white" />
                </div>
                <span className="text-xl font-bold tracking-tight">Traceable Health</span>
              </div>
              <h2 className="text-3xl font-bold leading-tight mb-4">
                Advanced Clinical Data Extraction & Analysis
              </h2>
              <p className="text-slate-400 leading-relaxed">
                Streamline your medical documentation workflow with our formal, AI-driven processing engine.
              </p>
           </div>

           <div className="space-y-4">
              <div className="flex items-center gap-3 text-sm text-slate-300">
                <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">1</div>
                <span>Secure local-first authentication</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-slate-300">
                <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">2</div>
                <span>HIPAA-compliant document processing</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-slate-300">
                <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">3</div>
                <span>Automated discharge summaries</span>
              </div>
           </div>
        </div>

        {/* Right Side - Form */}
        <div className="w-full md:w-7/12 p-12">
          <div className="max-w-md mx-auto">
             <h3 className="text-2xl font-bold text-slate-900 mb-2">
                {isLogin ? 'Welcome Back' : 'Create Account'}
             </h3>
             <p className="text-slate-500 mb-8">
                {isLogin ? 'Enter your credentials to access the dashboard.' : 'Register to start processing clinical documents.'}
             </p>

             {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-100 text-red-600 text-sm rounded-lg flex items-start gap-2">
                   <div className="mt-0.5 min-w-[4px] h-4 w-4 rounded-full bg-red-200 flex items-center justify-center text-[10px] font-bold">!</div>
                   {error}
                </div>
             )}

             {isLogin ? (
                 <form onSubmit={handleLoginSubmit} className="space-y-5">
                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-slate-700">Username</label>
                        <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-5 w-5" />
                            <input 
                                type="text"
                                value={formData.username}
                                onChange={e => setFormData({...formData, username: e.target.value})}
                                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition-all"
                                placeholder="username"
                            />
                        </div>
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-slate-700">Password</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-5 w-5" />
                            <input 
                                type="password"
                                value={formData.password}
                                onChange={e => setFormData({...formData, password: e.target.value})}
                                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition-all"
                                placeholder="••••••••"
                            />
                        </div>
                    </div>

                    <button 
                        type="submit"
                        disabled={loading}
                        className="w-full bg-slate-900 text-white py-2.5 rounded-lg font-medium hover:bg-slate-800 transition-colors flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
                    >
                        {loading ? (
                            <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                        ) : (
                            <>
                                Sign In
                                <ArrowRight size={18} />
                            </>
                        )}
                    </button>
                 </form>
             ) : (
                 <form onSubmit={step === 'details' ? handleSendCode : handleRegister} className="space-y-5">
                    {step === 'details' && (
                        <>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1.5">
                                    <label className="text-sm font-medium text-slate-700">Full Name</label>
                                    <input 
                                        type="text"
                                        required
                                        value={formData.name}
                                        onChange={e => setFormData({...formData, name: e.target.value})}
                                        className="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 outline-none"
                                        placeholder="Dr."
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-sm font-medium text-slate-700">Username</label>
                                    <input 
                                        type="text"
                                        required
                                        value={formData.username}
                                        onChange={e => setFormData({...formData, username: e.target.value})}
                                        className={`w-full px-4 py-2.5 rounded-lg border outline-none transition-all ${
                                            usernameError ? 'border-red-300 focus:ring-2 focus:ring-red-200' : 'border-slate-300 focus:ring-2 focus:ring-brand-500'
                                        }`}
                                        placeholder="jdoe123"
                                    />
                                    {usernameError && <p className="text-xs text-red-500 mt-1">{usernameError}</p>}
                                </div>
                            </div>
                            
                            <div className="space-y-1.5">
                                <label className="text-sm font-medium text-slate-700">Email Address</label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-5 w-5" />
                                    <input 
                                        type="email"
                                        required
                                        value={formData.email}
                                        onChange={e => setFormData({...formData, email: e.target.value})}
                                        className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 outline-none"
                                        placeholder="xxx@xx.com"
                                    />
                                </div>
                            </div>

                            <div className="space-y-1.5">
                                <label className="text-sm font-medium text-slate-700">Medical Organization</label>
                                <div className="relative">
                                    <Building className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-5 w-5" />
                                    <input 
                                        type="text"
                                        required
                                        value={formData.organization}
                                        onChange={e => setFormData({...formData, organization: e.target.value})}
                                        className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 outline-none"
                                        placeholder="Traceable Health"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1.5">
                                    <label className="text-sm font-medium text-slate-700">Password</label>
                                    <div className="relative">
                                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-5 w-5" />
                                        <input 
                                            type="password"
                                            required
                                            value={formData.password}
                                            onChange={e => setFormData({...formData, password: e.target.value})}
                                            className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 outline-none"
                                            placeholder="••••••••"
                                        />
                                    </div>
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-sm font-medium text-slate-700">Confirm</label>
                                    <div className="relative">
                                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-5 w-5" />
                                        <input 
                                            type="password"
                                            required
                                            value={formData.confirmPassword}
                                            onChange={e => setFormData({...formData, confirmPassword: e.target.value})}
                                            className={`w-full pl-10 pr-4 py-2.5 rounded-lg border outline-none transition-all ${
                                                !passwordsMatch ? 'border-red-300 focus:ring-red-200' : 'border-slate-300 focus:ring-brand-500'
                                            }`}
                                            placeholder="••••••••"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Password Requirements Visualization */}
                            <div className="bg-slate-50 p-3 rounded-lg grid grid-cols-2 gap-2">
                                <Requirement met={passwordCriteria.length} label="8+ Characters" />
                                <Requirement met={passwordCriteria.upper} label="Uppercase (A-Z)" />
                                <Requirement met={passwordCriteria.lower} label="Lowercase (a-z)" />
                                <Requirement met={passwordCriteria.number} label="Number (0-9)" />
                                {!passwordsMatch && formData.confirmPassword !== '' && (
                                     <div className="col-span-2 text-xs text-red-600 font-medium flex items-center gap-1 mt-1">
                                        <X size={12} /> Passwords do not match
                                     </div>
                                )}
                            </div>
                            
                            <button 
                                type="submit"
                                disabled={loading}
                                className="w-full bg-brand-600 text-white py-2.5 rounded-lg font-medium hover:bg-brand-700 transition-colors flex items-center justify-center gap-2"
                            >
                                {loading ? 'Sending...' : 'Verify & Next'}
                            </button>
                        </>
                    )}

                    {step === 'verification' && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                             <div className="mb-6 text-center">
                                <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <Mail className="h-8 w-8 text-green-600" />
                                </div>
                                <h4 className="text-lg font-semibold text-slate-900">Check your Email</h4>
                                <p className="text-sm text-slate-500 mt-1">
                                    We sent a verification code to <span className="font-medium text-slate-700">{formData.email}</span>
                                </p>
                             </div>

                             <div className="space-y-4">
                                <div className="space-y-1.5">
                                    <label className="text-sm font-medium text-slate-700">Verification Code</label>
                                    <input 
                                        type="text"
                                        required
                                        value={formData.verificationCode}
                                        onChange={e => setFormData({...formData, verificationCode: e.target.value})}
                                        className="w-full px-4 py-3 text-center text-2xl tracking-widest font-mono rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 outline-none"
                                        placeholder="123456"
                                        maxLength={6}
                                    />
                                </div>

                                <button 
                                    type="submit"
                                    disabled={loading}
                                    className="w-full bg-slate-900 text-white py-2.5 rounded-lg font-medium hover:bg-slate-800 transition-colors flex items-center justify-center gap-2"
                                >
                                    {loading ? 'Registering...' : 'Complete Registration'}
                                </button>
                                
                                <button
                                    type="button"
                                    onClick={() => setStep('details')}
                                    className="w-full text-sm text-slate-500 hover:text-slate-700"
                                >
                                    Go Back
                                </button>
                             </div>
                        </div>
                    )}
                 </form>
             )}

             <div className="mt-8 pt-6 border-t border-slate-100 text-center">
                <p className="text-sm text-slate-500">
                    {isLogin ? "Don't have an account?" : "Already have an account?"}
                    <button 
                        onClick={toggleMode}
                        className="ml-1.5 font-medium text-brand-600 hover:text-brand-800 transition-colors"
                    >
                        {isLogin ? 'Register now' : 'Sign in'}
                    </button>
                </p>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper component for password requirements
const Requirement = ({ met, label }: { met: boolean, label: string }) => (
    <div className={`flex items-center gap-1.5 text-xs transition-colors ${met ? 'text-emerald-600 font-medium' : 'text-slate-400'}`}>
        {met ? <Check size={12} className="text-emerald-500" /> : <div className="w-3 h-3 rounded-full border border-slate-300" />}
        {label}
    </div>
);

export default Auth;
