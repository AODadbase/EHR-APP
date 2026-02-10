import React, { useState, useEffect } from 'react';
import { Activity, ArrowRight, Lock, User, Mail, Building, Check, X, Eye, EyeOff } from 'lucide-react';
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
  
  // Password Visibility State
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

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
    
    // --- VALIDATION CHECKS ---
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

    setLoading(true);

    // --- BACKEND CALL ---
    try {
        const response = await fetch('http://localhost:8000/api/send-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: formData.email }),
        });

        const data = await response.json();

        if (response.ok) {
            // Success
            setStep('verification');
        } else {
            setError(data.detail || 'Failed to send verification code.');
        }
    } catch (err: any) {
        console.error("Connection Error:", err);
        setError('Could not connect to the backend server. Is Python running?');
    } finally {
        setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
        // Verify the code with Python
        const verifyResponse = await fetch('http://localhost:8000/api/verify-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                email: formData.email,
                code: formData.verificationCode 
            }),
        });

        if (!verifyResponse.ok) {
            throw new Error("Invalid verification code. Please try again.");
        }

        // If verified, proceed with registration
        const user = await authService.register({
            username: formData.username,
            password: formData.password,
            name: formData.name,
            email: formData.email,
            organization: formData.organization,
            role: 'doctor' 
        });
        
        onLogin(user);

    } catch (err: any) {
        setError(err.message || "Registration failed");
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
      setFormData({ ...formData, password: '', confirmPassword: '' });
      setShowPassword(false);
      setShowConfirmPassword(false);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 md:p-12">
      <div className="bg-white rounded-3xl shadow-2xl overflow-hidden flex max-w-6xl w-full border border-slate-100 min-h-[700px]">
        
        {/* Left Side - Brand / Decorative */}
        <div className="hidden md:flex flex-col justify-between w-5/12 bg-slate-900 p-16 text-white relative overflow-hidden">
           {/* Abstract Pattern */}
           <div className="absolute top-0 right-0 w-80 h-80 bg-brand-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
           <div className="absolute bottom-0 left-0 w-80 h-80 bg-blue-600/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2"></div>

           <div>
              <div className="flex items-center gap-4 mb-10">
                <div className="p-2.5 bg-brand-600 rounded-xl shadow-lg shadow-brand-900/50">
                  <Activity className="h-7 w-7 text-white" />
                </div>
                <span className="text-2xl font-bold tracking-tight">Traceable Health</span>
              </div>
              <h2 className="text-4xl font-bold leading-tight mb-6">
                Advanced Clinical Data Extraction & Analysis
              </h2>
              <p className="text-slate-400 leading-relaxed text-lg">
                Streamline your medical documentation workflow with our formal, AI-driven processing engine.
              </p>
           </div>

           <div className="space-y-6">
              <div className="flex items-center gap-4 text-slate-300">
                <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700 font-semibold shadow-inner">1</div>
                <span className="text-lg">Secure local-first authentication</span>
              </div>
              <div className="flex items-center gap-4 text-slate-300">
                <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700 font-semibold shadow-inner">2</div>
                <span className="text-lg">HIPAA-compliant document processing</span>
              </div>
              <div className="flex items-center gap-4 text-slate-300">
                <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700 font-semibold shadow-inner">3</div>
                <span className="text-lg">Automated discharge summaries</span>
              </div>
           </div>
        </div>

        {/* Right Side - Form */}
        <div className="w-full md:w-7/12 p-16 flex flex-col justify-center">
          <div className="max-w-lg mx-auto w-full">
             <div className="mb-10">
                <h3 className="text-3xl font-bold text-slate-900 mb-3">
                    {isLogin ? 'Welcome Back' : 'Create Account'}
                </h3>
                <p className="text-lg text-slate-500">
                    {isLogin ? 'Enter your credentials to access the dashboard.' : 'Register to start processing clinical documents.'}
                </p>
             </div>

             {error && (
                <div className="mb-8 p-4 bg-red-50 border border-red-100 text-red-600 text-sm rounded-xl flex items-start gap-3">
                   <div className="mt-0.5 min-w-[20px] h-5 w-5 rounded-full bg-red-200 flex items-center justify-center text-xs font-bold">!</div>
                   <span className="leading-snug">{error}</span>
                </div>
             )}

             {isLogin ? (
                 <form onSubmit={handleLoginSubmit} className="space-y-7">
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-slate-700 ml-1">Username</label>
                        <div className="relative">
                            <User className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 h-5 w-5" />
                            <input 
                                type="text"
                                value={formData.username}
                                onChange={e => setFormData({...formData, username: e.target.value})}
                                className="w-full pl-12 pr-4 py-3.5 rounded-xl border border-slate-300 focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all text-base"
                                placeholder="username"
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-slate-700 ml-1">Password</label>
                        <div className="relative">
                            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 h-5 w-5" />
                            <input 
                                type={showPassword ? "text" : "password"}
                                value={formData.password}
                                onChange={e => setFormData({...formData, password: e.target.value})}
                                className="w-full pl-12 pr-12 py-3.5 rounded-xl border border-slate-300 focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all text-base"
                                placeholder="••••••••"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                            >
                                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                            </button>
                        </div>
                    </div>

                    <button 
                        type="submit"
                        disabled={loading}
                        className="w-full bg-slate-900 text-white py-4 rounded-xl font-semibold text-lg hover:bg-slate-800 transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-3 disabled:opacity-70 disabled:cursor-not-allowed mt-4"
                    >
                        {loading ? (
                            <span className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                        ) : (
                            <>
                                Sign In
                                <ArrowRight size={20} />
                            </>
                        )}
                    </button>
                 </form>
             ) : (
                 <form onSubmit={step === 'details' ? handleSendCode : handleRegister} className="space-y-7">
                    {step === 'details' && (
                        <>
                            <div className="grid grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label className="text-sm font-semibold text-slate-700 ml-1">Full Name</label>
                                    <input 
                                        type="text"
                                        required
                                        value={formData.name}
                                        onChange={e => setFormData({...formData, name: e.target.value})}
                                        className="w-full px-4 py-3.5 rounded-xl border border-slate-300 focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all"
                                        placeholder="Dr."
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-semibold text-slate-700 ml-1">Username</label>
                                    <input 
                                        type="text"
                                        required
                                        value={formData.username}
                                        onChange={e => setFormData({...formData, username: e.target.value})}
                                        className={`w-full px-4 py-3.5 rounded-xl border outline-none transition-all focus:ring-4 ${
                                            usernameError 
                                            ? 'border-red-300 focus:ring-red-100 focus:border-red-500' 
                                            : 'border-slate-300 focus:ring-brand-100 focus:border-brand-500'
                                        }`}
                                        placeholder="username"
                                    />
                                    {usernameError && <p className="text-xs text-red-500 mt-1 ml-1 font-medium">{usernameError}</p>}
                                </div>
                            </div>
                            
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-slate-700 ml-1">Email Address</label>
                                <div className="relative">
                                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 h-5 w-5" />
                                    <input 
                                        type="email"
                                        required
                                        value={formData.email}
                                        onChange={e => setFormData({...formData, email: e.target.value})}
                                        className="w-full pl-12 pr-4 py-3.5 rounded-xl border border-slate-300 focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all"
                                        placeholder="xxx@xx.com"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-slate-700 ml-1">Medical Organization</label>
                                <div className="relative">
                                    <Building className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 h-5 w-5" />
                                    <input 
                                        type="text"
                                        required
                                        value={formData.organization}
                                        onChange={e => setFormData({...formData, organization: e.target.value})}
                                        className="w-full pl-12 pr-4 py-3.5 rounded-xl border border-slate-300 focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all"
                                        placeholder="Traceable Health"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label className="text-sm font-semibold text-slate-700 ml-1">Password</label>
                                    <div className="relative">
                                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 h-5 w-5" />
                                        <input 
                                            type={showPassword ? "text" : "password"}
                                            required
                                            value={formData.password}
                                            onChange={e => setFormData({...formData, password: e.target.value})}
                                            className="w-full pl-12 pr-12 py-3.5 rounded-xl border border-slate-300 focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all"
                                            placeholder="••••••••"
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowPassword(!showPassword)}
                                            className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                                        >
                                            {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                        </button>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-semibold text-slate-700 ml-1">Confirm</label>
                                    <div className="relative">
                                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 h-5 w-5" />
                                        <input 
                                            type={showConfirmPassword ? "text" : "password"}
                                            required
                                            value={formData.confirmPassword}
                                            onChange={e => setFormData({...formData, confirmPassword: e.target.value})}
                                            className={`w-full pl-12 pr-12 py-3.5 rounded-xl border outline-none transition-all focus:ring-4 ${
                                                !passwordsMatch 
                                                ? 'border-red-300 focus:ring-red-100 focus:border-red-500' 
                                                : 'border-slate-300 focus:ring-brand-100 focus:border-brand-500'
                                            }`}
                                            placeholder="••••••••"
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                            className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                                        >
                                            {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* Password Requirements Visualization */}
                            <div className="bg-slate-50 p-5 rounded-xl grid grid-cols-2 gap-3 border border-slate-100">
                                <Requirement met={passwordCriteria.length} label="8+ Characters" />
                                <Requirement met={passwordCriteria.upper} label="Uppercase (A-Z)" />
                                <Requirement met={passwordCriteria.lower} label="Lowercase (a-z)" />
                                <Requirement met={passwordCriteria.number} label="Number (0-9)" />
                                {!passwordsMatch && formData.confirmPassword !== '' && (
                                     <div className="col-span-2 text-sm text-red-600 font-medium flex items-center gap-2 mt-2 pt-2 border-t border-slate-200">
                                        <X size={14} /> Passwords do not match
                                     </div>
                                )}
                            </div>
                            
                            <button 
                                type="submit"
                                disabled={loading}
                                className="w-full bg-brand-600 text-white py-4 rounded-xl font-semibold text-lg hover:bg-brand-700 transition-all shadow-lg hover:shadow-brand-900/20 flex items-center justify-center gap-3 mt-4"
                            >
                                {loading ? 'Sending...' : 'Verify & Next'}
                            </button>
                        </>
                    )}

                    {step === 'verification' && (
                        <div className="animate-in fade-in slide-in-from-right-8 duration-500">
                             <div className="mb-10 text-center">
                                <div className="w-20 h-20 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-6 shadow-sm border border-green-100">
                                    <Mail className="h-10 w-10 text-green-600" />
                                </div>
                                <h4 className="text-2xl font-bold text-slate-900">Check your Email</h4>
                                <p className="text-slate-500 mt-2 text-lg">
                                    We sent a verification code to <br/>
                                    <span className="font-semibold text-slate-800">{formData.email}</span>
                                </p>
                             </div>

                             <div className="space-y-6">
                                <div className="space-y-3">
                                    <label className="text-sm font-semibold text-slate-700 block text-center">Enter Verification Code</label>
                                    <input 
                                        type="text"
                                        required
                                        value={formData.verificationCode}
                                        onChange={e => setFormData({...formData, verificationCode: e.target.value})}
                                        className="w-full px-4 py-4 text-center text-3xl tracking-[0.5em] font-mono rounded-xl border border-slate-300 focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all"
                                        placeholder="123456"
                                        maxLength={6}
                                    />
                                </div>

                                <button 
                                    type="submit"
                                    disabled={loading}
                                    className="w-full bg-slate-900 text-white py-4 rounded-xl font-semibold text-lg hover:bg-slate-800 transition-all shadow-lg flex items-center justify-center gap-3"
                                >
                                    {loading ? 'Registering...' : 'Complete Registration'}
                                </button>
                                
                                <button
                                    type="button"
                                    onClick={() => setStep('details')}
                                    className="w-full text-slate-500 hover:text-slate-800 transition-colors font-medium"
                                >
                                    Go Back
                                </button>
                             </div>
                        </div>
                    )}
                 </form>
             )}

             <div className="mt-10 pt-8 border-t border-slate-100 text-center">
                <p className="text-slate-500">
                    {isLogin ? "Don't have an account?" : "Already have an account?"}
                    <button 
                        onClick={toggleMode}
                        className="ml-2 font-bold text-brand-600 hover:text-brand-800 transition-colors"
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
    <div className={`flex items-center gap-2 text-sm transition-colors ${met ? 'text-emerald-700 font-semibold' : 'text-slate-400'}`}>
        {met ? <Check size={16} className="text-emerald-500" /> : <div className="w-4 h-4 rounded-full border border-slate-300 bg-white" />}
        {label}
    </div>
);

export default Auth;